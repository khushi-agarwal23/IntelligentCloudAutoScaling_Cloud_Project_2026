from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CheckoutRequest(BaseModel):
    user_id: Optional[int] = None
    product: str = Field(..., min_length=1, description="Product description or name")
    amount: float = Field(..., gt=0, description="Purchase amount")
    items_count: int = Field(1, ge=1, description="Number of items in cart")
    payment_method: str = Field("credit_card", description="Payment method: credit_card, upi, net_banking")


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    order_id: str
    product: str
    amount: float
    items_count: int
    payment_method: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionStatsResponse(BaseModel):
    total_transactions: int
    total_revenue: float
    average_order_value: float
    completed_count: int
    failed_count: int
