"""Data-access layer (CRUD + analytics queries)."""
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app import models, schemas


# ----- Audit -----
def write_audit(db: Session, *, username, role, action, resource, detail, status_code) -> None:
    db.add(models.AuditLog(
        username=username, role=role, action=action,
        resource=resource, detail=detail, status_code=status_code,
    ))
    db.commit()


def get_audit_logs(db: Session, limit: int = 200) -> list[models.AuditLog]:
    return list(db.scalars(select(models.AuditLog).order_by(models.AuditLog.id.desc()).limit(limit)))


# ----- Customers -----
def create_customer(db: Session, payload: schemas.CustomerCreate) -> models.Customer:
    customer = models.Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_customers(db: Session, skip: int = 0, limit: int = 100) -> list[models.Customer]:
    return list(db.scalars(select(models.Customer).offset(skip).limit(limit)))


def get_customer(db: Session, customer_id: int) -> models.Customer | None:
    return db.get(models.Customer, customer_id)


def get_customer_by_email(db: Session, email: str) -> models.Customer | None:
    return db.scalar(select(models.Customer).where(models.Customer.email == email))


def update_customer(db: Session, customer: models.Customer, payload: schemas.CustomerUpdate) -> models.Customer:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return customer


# ----- Orders -----
def create_order(db: Session, payload: schemas.OrderCreate) -> models.Order:
    order = models.Order(**payload.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_orders(db: Session, skip: int = 0, limit: int = 100) -> list[models.Order]:
    return list(db.scalars(select(models.Order).offset(skip).limit(limit)))


# ----- Dashboard analytics -----
def get_dashboard_metrics(db: Session) -> schemas.DashboardMetrics:
    total_revenue = db.scalar(select(func.coalesce(func.sum(models.Order.amount), 0))) or 0
    total_orders = db.scalar(select(func.count(models.Order.order_id))) or 0
    total_customers = db.scalar(select(func.count(models.Customer.customer_id))) or 0

    top_rows = db.execute(
        select(
            models.Customer.customer_id,
            models.Customer.name,
            func.coalesce(func.sum(models.Order.amount), 0).label("total_spent"),
            func.count(models.Order.order_id).label("order_count"),
        )
        .join(models.Order, models.Order.customer_id == models.Customer.customer_id)
        .group_by(models.Customer.customer_id, models.Customer.name)
        .order_by(desc("total_spent"))
        .limit(5)
    ).all()

    city_rows = db.execute(
        select(
            func.coalesce(models.Customer.city, "Unknown").label("city"),
            func.coalesce(func.sum(models.Order.amount), 0).label("revenue"),
        )
        .join(models.Order, models.Order.customer_id == models.Customer.customer_id)
        .group_by(models.Customer.city)
        .order_by(desc("revenue"))
    ).all()

    return schemas.DashboardMetrics(
        total_revenue=total_revenue,
        total_orders=total_orders,
        total_customers=total_customers,
        top_customers=[
            schemas.TopCustomer(
                customer_id=r.customer_id, name=r.name, total_spent=r.total_spent, order_count=r.order_count
            )
            for r in top_rows
        ],
        revenue_by_city=[schemas.CityRevenue(city=r.city, revenue=r.revenue) for r in city_rows],
    )
