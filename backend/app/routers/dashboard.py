"""Dashboard analytics endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=schemas.DashboardMetrics)
def dashboard_metrics(db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    return crud.get_dashboard_metrics(db)
