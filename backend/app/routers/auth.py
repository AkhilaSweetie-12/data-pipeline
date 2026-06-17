"""Authentication endpoints (login, current user) and audit log access."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("retail_api")


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        crud.write_audit(db, username=form_data.username, role=None, action="LOGIN",
                         resource="auth", detail="failed login", status_code=401)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = auth.create_access_token(user.username, user.role)
    crud.write_audit(db, username=user.username, role=user.role, action="LOGIN",
                     resource="auth", detail="successful login", status_code=200)
    return schemas.Token(access_token=token, role=user.role, username=user.username)


@router.get("/me", response_model=schemas.UserOut)
def me(user=Depends(auth.get_current_user)):
    return user


@router.get("/audit", response_model=list[schemas.AuditLogOut])
def audit_logs(db: Session = Depends(get_db), user=Depends(auth.require_roles("admin"))):
    return crud.get_audit_logs(db)
