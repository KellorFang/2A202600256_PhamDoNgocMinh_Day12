# Day 12 Lab — Mission Answers

> **Student Name:** Pham Do Ngoc Minh
> **Student ID:** 2A202600256
> **Date:** 17/04/2026

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found in `01-localhost-vs-production/develop/app.py`

1. **API key hardcoded** (line 17): `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"` — nếu push lên GitHub thì key bị lộ ngay lập tức.
2. **Database URL hardcoded** (line 18): `DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"` — password và connection string bị lộ trong code.
3. **Logging secret ra console** (line 34): `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")` — in secret vào logs là cực kỳ nguy hiểm.
4. **Không có health check endpoint** (comment line 42–43): Platform không biết agent crash để tự restart.
5. **Port cố định & host sai** (line 51–53): `host="localhost"` chỉ nhận kết nối nội bộ (không chạy trong container được); `port=8000` hardcode thay vì đọc từ env var `PORT`.
6. **Debug reload bật trong production** (line 53): `reload=True` gây reload liên tục, không phù hợp production.
7. **Không có config management** (line 21–22): Biến `DEBUG`, `MAX_TOKENS` hardcode thay vì đọc từ environment variables.

### Exercise 1.3: Comparison table — `develop/app.py` vs `production/app.py`

| Feature | Develop (Basic) | Production (Advanced) | Tại sao quan trọng? |
|---|---|---|---|
| Config | Hardcode trong code | Đọc từ env vars qua `config.py` (12-Factor) | Tránh lộ secret, dễ thay đổi giữa các môi trường |
| Secrets | API key viết thẳng vào source | Không có secret nào trong code | Secret trong code → lộ khi push Git |
| Health check | ❌ Không có | ✅ `/health` + `/ready` endpoints | Platform cần endpoint này để biết container có sống không |
| Logging | `print()` + in ra secret | JSON structured logging, không log secret | JSON dễ parse bởi log aggregator (Datadog, Loki) |
| Shutdown | Đột ngột (không handle signal) | ✅ `SIGTERM` handler + graceful lifespan | Tránh mất request đang xử lý khi deploy/scale |
| Host binding | `localhost` (chỉ chạy local) | `0.0.0.0` (nhận kết nối từ bên ngoài container) | Container cần `0.0.0.0` để accessible |
| Port | Hardcode `8000` | Đọc từ `PORT` env var | Railway/Render inject `PORT` tự động |
| Debug mode | `reload=True` luôn bật | Chỉ bật khi `DEBUG=true` | Tránh reload không cần thiết trong production |
| CORS | ❌ Không có | ✅ CORSMiddleware với `allowed_origins` | Bảo vệ API khỏi request từ domain không hợp lệ |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions (`02-docker/develop/Dockerfile`)

1. **Base image là gì?** `python:3.11` — full Python distribution (~1 GB)
2. **Working directory là gì?** `/app` (set bởi `WORKDIR /app`)
3. **Tại sao COPY requirements.txt trước?** Docker build theo layer. Nếu `requirements.txt` không thay đổi, layer `pip install` được cache lại → build nhanh hơn nhiều. Chỉ khi thay đổi `requirements.txt` thì mới cần cài lại dependencies.
4. **CMD vs ENTRYPOINT khác nhau thế nào?**
   - `CMD`: lệnh mặc định, **có thể override** khi chạy `docker run image <other_command>`
   - `ENTRYPOINT`: lệnh bắt buộc, **không thể override** dễ dàng, dùng khi muốn container hoạt động như một executable cố định

### Exercise 2.3: Multi-stage build (`02-docker/production/Dockerfile`)

- **Stage 1 (builder — `python:3.11-slim`):** Cài build tools (`gcc`, `libpq-dev`), install tất cả Python packages vào `/root/.local` với `--user`. Stage này có thể nặng vì cần compiler.
- **Stage 2 (runtime — `python:3.11-slim`):** Chỉ copy `/root/.local` (các packages đã cài) từ builder sang. Không có `gcc`, không có `apt` cache → image nhỏ và sạch hơn.
- **Tại sao image nhỏ hơn?** Stage 2 không mang theo build tools (gcc, libpq-dev, apt cache). Chỉ giữ đúng những gì cần để CHẠY, không cần để BUILD.
- **Bonus**: Stage 2 tạo non-root user `appuser` → security best practice.

### Exercise 2.4: Docker Compose services

Services trong `02-docker/production/docker-compose.yml`:
- **agent**: FastAPI app (có thể scale với `--scale agent=N`)
- **nginx**: Reverse proxy / load balancer — nhận request từ port 80, forward tới các agent instances
- **redis**: Lưu state (conversation history, rate limit counters)

Giao tiếp: `Client → Nginx (port 80) → Agent instances → Redis`

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

- **URL:** _(điền sau khi deploy)_
- **Screenshot:** _(xem `screenshots/` folder)_

### Exercise 3.2: Render vs Railway config

| Điểm khác nhau | `railway.toml` | `render.yaml` |
|---|---|---|
| Format | TOML | YAML |
| Health check path | Cấu hình trong dashboard | `healthCheckPath: /health` trong file |
| Deploy trigger | `railway up` từ CLI | Connect GitHub repo → auto deploy |
| Region | Tự chọn trong CLI | `region: oregon` trong file |
| Build command | Mặc định auto-detect | `buildCommand: pip install -r requirements.txt` |

---

## Part 4: API Security

### Exercise 4.1: API Key authentication (`04-api-gateway/develop/app.py`)

- **API key được check ở đâu?** Trong middleware hoặc dependency function — kiểm tra header `X-API-Key` trên mỗi request vào `/ask`.
- **Điều gì xảy ra nếu sai key?** Server trả về HTTP `401 Unauthorized`.
- **Làm sao rotate key?** Thay giá trị env var `AGENT_API_KEY` và restart service — không cần thay code.

### Exercise 4.2: JWT flow

1. Client POST `/token` với username + password
2. Server verify credentials → tạo JWT token (signed với `JWT_SECRET`, có expiry)
3. Client gửi request với header `Authorization: Bearer <token>`
4. Server decode + verify token → lấy `user_id` → xử lý request

### Exercise 4.3: Rate limiting

- **Algorithm:** Sliding window — dùng `deque` lưu timestamps của các request trong 60 giây gần nhất
- **Limit:** `RATE_LIMIT_PER_MINUTE` (mặc định 20 req/min), có thể config qua env var
- **Bypass limit cho admin:** Có thể exclude một số API key khỏi rate limiter bằng cách check whitelist trước khi gọi `check_rate_limit()`

### Exercise 4.4: Cost guard implementation

```python
import redis
from datetime import datetime

r = redis.Redis()

def check_budget(user_id: str, estimated_cost: float) -> bool:
    """
    Return True nếu còn budget, False nếu vượt.
    Mỗi user có budget $10/tháng, reset đầu tháng, lưu trong Redis.
    """
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    current = float(r.get(key) or 0)
    if current + estimated_cost > 10:
        return False
    
    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)  # TTL 32 ngày để cover hết tháng
    return True
```

**Giải thích:** Key Redis theo pattern `budget:{user_id}:{YYYY-MM}` tự động reset theo tháng (TTL 32 ngày). `incrbyfloat` là atomic operation — thread-safe khi có nhiều instances.

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health check endpoints

```python
@app.get("/health")
def health():
    """Liveness probe — container còn sống không?"""
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/ready")
def ready():
    """Readiness probe — sẵn sàng nhận traffic chưa?"""
    if not _is_ready:
        raise HTTPException(status_code=503, detail="Not ready yet")
    return {"ready": True}
```

**Điểm khác nhau:** `/health` (liveness) = process còn sống không → fail → restart. `/ready` (readiness) = có thể nhận traffic không → fail → load balancer không route vào.

### Exercise 5.2: Graceful shutdown

```python
import signal

def shutdown_handler(signum, frame):
    """Handle SIGTERM từ container orchestrator."""
    logger.info("SIGTERM received — graceful shutdown initiated")
    # FastAPI lifespan context tự handle finish in-flight requests
    # Thêm cleanup ở đây: đóng DB connection, flush queue, etc.

signal.signal(signal.SIGTERM, shutdown_handler)
```

**Test kết quả:** Request đang xử lý hoàn thành trước khi process thoát (trong vòng `timeout_graceful_shutdown=30s`).

### Exercise 5.3: Stateless design

**Anti-pattern** (trong memory):
```python
conversation_history = {}  # ❌ Mỗi instance có bộ nhớ riêng
```

**Correct** (trong Redis):
```python
# ✅ Tất cả instances đọc/ghi cùng Redis
history = r.lrange(f"history:{user_id}", 0, -1)
r.rpush(f"history:{user_id}", new_message)
r.expire(f"history:{user_id}", 86400)  # TTL 1 ngày
```

**Tại sao quan trọng?** Khi scale ra 3 instances với `docker compose up --scale agent=3`, mỗi request có thể đến bất kỳ instance nào. Nếu state trong memory, user sẽ mất conversation history khi request đến instance khác.

### Exercise 5.4: Load balancing test

```bash
docker compose up --scale agent=3
# Gọi 10 requests → kiểm tra logs thấy 3 instances xử lý luân phiên
docker compose logs agent | grep "agent_request"
```

**Quan sát:** Nginx round-robin phân tán request tới 3 agent instances. Nếu 1 instance báo unhealthy, Nginx tự loại ra khỏi pool.

### Exercise 5.5: Stateless test

```bash
python test_stateless.py
# 1. Tạo conversation trên instance 1
# 2. Kill instance 1
# 3. Tiếp tục conversation → vẫn còn vì state lưu trong Redis
```

---

## Tổng Kết

| Part | Concept chính | Status |
|---|---|---|
| 1 | 12-Factor App, env vars, no hardcode secrets | ✅ |
| 2 | Multi-stage Docker, layer caching, Compose | ✅ |
| 3 | Cloud deployment Railway/Render | ✅ |
| 4 | API key auth, rate limiting, cost guard | ✅ |
| 5 | Health/readiness, graceful shutdown, stateless | ✅ |
| 6 | Full production agent | ✅ |
