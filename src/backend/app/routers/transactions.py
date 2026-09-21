import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from ..database import get_db
from ..models.user import User
from ..models.transaction import Transaction
from ..schemas.transaction import CheckoutRequest, TransactionResponse, TransactionStatsResponse
from .auth import get_current_user, oauth2_scheme
from ..utils.security import decode_access_token

router = APIRouter(prefix="/transactions", tags=["Transactions & Flash Sales"])


@router.post("/checkout", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    checkout_in: CheckoutRequest,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Simulates high-speed checkout and order placement during festival flash sales.
    Accepts authenticated user via JWT or explicit user_id.
    """
    user_id = checkout_in.user_id
    if not user_id and token:
        payload = decode_access_token(token)
        if payload and "user_id" in payload:
            user_id = payload["user_id"]

    if not user_id:
        # Check if a fallback demo user exists, else create one
        demo_user = db.scalar(select(User).limit(1))
        if demo_user:
            user_id = demo_user.id
        else:
            demo = User(email="guest_festival@example.com", hashed_password="guest_demo_hash", full_name="Guest Shopper")
            db.add(demo)
            db.commit()
            db.refresh(demo)
            user_id = demo.id
    else:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    order_id = f"ORD-FEST-{uuid.uuid4().hex[:8].upper()}"

    transaction = Transaction(
        user_id=user_id,
        order_id=order_id,
        product=checkout_in.product,
        amount=checkout_in.amount,
        items_count=checkout_in.items_count,
        payment_method=checkout_in.payment_method,
        status="completed"
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    user_id: Optional[int] = Query(None, description="Filter transactions by user ID"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieves list of transactions with optional user filter."""
    stmt = select(Transaction).order_by(desc(Transaction.created_at)).limit(limit)
    if user_id is not None:
        stmt = stmt.where(Transaction.user_id == user_id)
    return list(db.scalars(stmt).all())


@router.get("/stats", response_model=TransactionStatsResponse)
def get_transaction_stats(db: Session = Depends(get_db)):
    """Calculates festival sales metrics: total revenue, order count, AOV."""
    total_tx = db.scalar(select(func.count(Transaction.id))) or 0
    total_rev = db.scalar(select(func.sum(Transaction.amount))) or 0.0
    completed = db.scalar(select(func.count(Transaction.id)).where(Transaction.status == "completed")) or 0
    failed = db.scalar(select(func.count(Transaction.id)).where(Transaction.status == "failed")) or 0
    aov = round(total_rev / total_tx, 2) if total_tx > 0 else 0.0

    return {
        "total_transactions": total_tx,
        "total_revenue": round(float(total_rev), 2),
        "average_order_value": aov,
        "completed_count": completed,
        "failed_count": failed
    }


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Retrieves a specific transaction by ID."""
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx
