import uuid
from typing import List
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class PaymentType(str, Enum):
    cash = "cash"
    cashless = "cashless"


class ProductBase(BaseModel):
    name: str
    price: float = Field(..., gt=0)
    quantity: float = Field(..., gt=0)


class Product(ProductBase):
    total: float

    @field_validator("total", mode="after")
    def round_total(cls, value):
        return round(value, 2)


class Payment(BaseModel):
    type: PaymentType
    amount: float = Field(..., gt=0)


class ReceiptCreate(BaseModel):
    products: List[ProductBase]
    payment: Payment


class Receipt(BaseModel):
    id: uuid.UUID
    products: List[Product]
    payment: Payment
    total: float
    rest: float
    user_id: uuid.UUID
    public_url: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
