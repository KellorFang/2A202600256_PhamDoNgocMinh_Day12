"""
app/auth.py — API Key Authentication

Mục đích:
  - Bảo vệ endpoint /ask: chỉ cho phép request có X-API-Key hợp lệ
  - Trả về 401 Unauthorized nếu key sai hoặc thiếu

Tại sao cần?
  - Public URL = ai cũng gọi được → tốn tiền OpenAI
  - Auth là tuyến phòng thủ đầu tiên
"""

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from app.config import settings

# FastAPI sẽ tự động đọc header "X-API-Key" từ mỗi request
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Dependency function — inject vào endpoint với Depends(verify_api_key).

    Returns:
        api_key (str): key hợp lệ (dùng làm user identifier)

    Raises:
        HTTPException 401: nếu key sai hoặc không có
    """
    if not api_key or api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include header: X-API-Key: <your-key>",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key
