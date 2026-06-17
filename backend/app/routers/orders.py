"""Order endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import get_db

router = APIRouter(prefix="/orders", tags=["orders"])
logger = logging.getLogger("retail_api")


@router.post("", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(payload: schemas.OrderCreate, db: Session = Depends(get_db),
                 user=Depends(auth.require_roles(*auth.WRITE_ROLES))):
    if not crud.get_customer(db, payload.customer_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="customer_id does not exist")
    order = crud.create_order(db, payload)
    crud.write_audit(db, username=user.username, role=user.role, action="CREATE",
                     resource="orders", detail=f"order_id={order.order_id}", status_code=201)
    logger.info("Created order id=%s for customer=%s by %s", order.order_id, order.customer_id, user.username)
    return order


@router.get("", response_model=list[schemas.OrderOut])
def list_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                user=Depends(auth.get_current_user)):
    return crud.get_orders(db, skip=skip, limit=limit)
