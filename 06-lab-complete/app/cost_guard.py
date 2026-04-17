"""
app/cost_guard.py — Cost Guard (Budget Protection)

Mục đích:
  - Tính chi phí ước tính của mỗi request (dựa trên token count)
  - Dừng service khi vượt budget ngày để tránh bill shock

Tại sao cần?
  - Gọi OpenAI API tốn tiền thật
  - Không có cost guard → 1 bug loop có thể tiêu hết $100 trong vài phút

Cách tính:
  - GPT-4o-mini: ~$0.00015/1K input tokens, ~$0.0006/1K output tokens
  - Estimate: số từ * 2 ≈ số tokens (ước tính thô)
"""

import time

from fastapi import HTTPException

from app.config import settings

# State in-memory (production thật dùng Redis)
_daily_cost: float = 0.0
_cost_reset_day: str = time.strftime("%Y-%m-%d")


def check_and_record_cost(input_tokens: int, output_tokens: int) -> None:
    """
    Kiểm tra và ghi nhận chi phí của request.

    Args:
        input_tokens: số token đầu vào (câu hỏi)
        output_tokens: số token đầu ra (câu trả lời)

    Raises:
        HTTPException 503: nếu đã vượt budget ngày
    """
    global _daily_cost, _cost_reset_day

    # Reset cost vào đầu ngày mới
    today = time.strftime("%Y-%m-%d")
    if today != _cost_reset_day:
        _daily_cost = 0.0
        _cost_reset_day = today

    # Kiểm tra budget trước khi xử lý
    if _daily_cost >= settings.daily_budget_usd:
        raise HTTPException(
            status_code=503,
            detail=f"Daily budget of ${settings.daily_budget_usd} exhausted. Service resumes tomorrow.",
        )

    # Tính cost và cộng vào tổng
    # Giá GPT-4o-mini (ước tính)
    cost = (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006
    _daily_cost += cost


def get_daily_cost() -> float:
    """Trả về chi phí đã dùng trong ngày hôm nay."""
    return round(_daily_cost, 6)
