"""Pydantic schemas for request/response validation."""
from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ----- Customer -----
class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    city: str | None = Field(default=None, max_length=120)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    city: str | None = Field(default=None, max_length=120)


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    created_at: datetime


# ----- Order -----
class OrderBase(BaseModel):
    customer_id: int
    product_name: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0)
    order_date: date


class OrderCreate(OrderBase):
    pass


class OrderOut(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    created_at: datetime


# ----- Auth -----
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str | None
    role: str | None
    action: str
    resource: str
    detail: str | None
    status_code: int
    created_at: datetime


# ----- Dashboard -----
class TopCustomer(BaseModel):
    customer_id: int
    name: str
    total_spent: Decimal
    order_count: int


class CityRevenue(BaseModel):
    city: str
    revenue: Decimal


class DashboardMetrics(BaseModel):
    total_revenue: Decimal
    total_orders: int
    total_customers: int
    top_customers: list[TopCustomer]
    revenue_by_city: list[CityRevenue]
