"""Customer endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import get_db

router = APIRouter(prefix="/customers", tags=["customers"])
logger = logging.getLogger("retail_api")


@router.post("", response_model=schemas.CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(payload: schemas.CustomerCreate, db: Session = Depends(get_db),
                    user=Depends(auth.require_roles(*auth.WRITE_ROLES))):
    if crud.get_customer_by_email(db, payload.email):
        logger.warning("Duplicate customer email rejected: %s", payload.email)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    customer = crud.create_customer(db, payload)
    crud.write_audit(db, username=user.username, role=user.role, action="CREATE",
                     resource="customers", detail=f"customer_id={customer.customer_id}", status_code=201)
    logger.info("Created customer id=%s by %s", customer.customer_id, user.username)
    return customer


@router.get("", response_model=list[schemas.CustomerOut])
def list_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                   user=Depends(auth.get_current_user)):
    return crud.get_customers(db, skip=skip, limit=limit)


@router.put("/{customer_id}", response_model=schemas.CustomerOut)
def update_customer(customer_id: int, payload: schemas.CustomerUpdate, db: Session = Depends(get_db),
                    user=Depends(auth.require_roles(*auth.WRITE_ROLES))):
    customer = crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    if payload.email and payload.email != customer.email:
        existing = crud.get_customer_by_email(db, payload.email)
        if existing and existing.customer_id != customer_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    updated = crud.update_customer(db, customer, payload)
    crud.write_audit(db, username=user.username, role=user.role, action="UPDATE",
                     resource="customers", detail=f"customer_id={customer_id}", status_code=200)
    logger.info("Updated customer id=%s by %s", customer_id, user.username)
    return updated
