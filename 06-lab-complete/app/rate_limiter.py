"""
app/rate_limiter.py — Rate Limiting (Sliding Window)

Mục đích:
  - Giới hạn số request mỗi user gửi trong 1 phút
  - Trả về 429 Too Many Requests khi vượt giới hạn

Tại sao cần?
  - Không có rate limit → 1 user có thể spam thousands request
  - Tốn tiền gọi LLM, làm chậm server cho người khác

Algorithm: Sliding Window
  - Lưu timestamps của các request trong 60 giây qua
  - Nếu số request >= limit → reject
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException

from app.config import settings

# In-memory store: key → deque of timestamps
# Trong production thật: dùng Redis để share state giữa nhiều instances
_rate_windows: dict[str, deque] = defaultdict(deque)


def check_rate_limit(key: str) -> None:
    """
    Kiểm tra rate limit cho một key (thường là API key hoặc user ID).

    Args:
        key: identifier của user/client

    Raises:
        HTTPException 429: nếu vượt rate limit
    """
    now = time.time()
    window = _rate_windows[key]

    # Xóa timestamps cũ hơn 60 giây
    while window and window[0] < now - 60:
        window.popleft()

    # Kiểm tra giới hạn
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} requests/minute. Try again later.",
            headers={"Retry-After": "60"},
        )

    # Ghi lại timestamp của request này
    window.append(now)
