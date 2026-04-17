# Deployment Information

## Public URL
https://believable-hope-production-38c3.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```bash
curl https://believable-hope-production-38c3.up.railway.app/health
# Expected: {"status": "ok", "version": "1.0.0", "environment": "production", ...}
```

### API Test (with authentication)
```bash
curl -X POST https://believable-hope-production-38c3.up.railway.app/ask \
  -H "X-API-Key: my-production-key-day12" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# Expected: {"question": "Hello", "answer": "...", "model": "gpt-4o-mini", ...}
```

### Missing/Invalid API Key Test
```bash
curl -X POST https://believable-hope-production-38c3.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# Expected: {"detail": "Invalid or missing API key. Include header: X-API-Key: <key>"}
```

## Environment Variables Set
- `PORT` (Provided by Railway / Nixpacks automatically)
- `ENVIRONMENT` (Set to "production")
- `AGENT_API_KEY`
- `JWT_SECRET`
- `LOG_LEVEL` (Optional, defaults to INFO)

## Screenshots
*(Lưu ý: Học viên tự chụp screenshot và thả vào folder `screenshots/` theo yêu cầu)*
- [Deployment dashboard](screenshots/dashboard.jpg)
- [Service running logs](screenshots/running.jpg)
- [Test results from Postman/Terminal](screenshots/test.jpg)
