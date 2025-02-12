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

    @field_validator("total", mode="before")
    def calculate_total(self, v, values):
        if "price" in values.data and "quantity" in values.data:
            return round(values.data["price"] * values.data["quantity"], 2)
        return v


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
    created_at: datetime
    user_id: uuid.UUID
    public_url: str | None = None

    class Config:
        from_attributes = True


class ShortLinkBase(BaseModel):
    short_code: str


class ShortLink(ShortLinkBase):
    id: int
    receipt_id: uuid.UUID

    class Config:
        from_attributes = True


class ReceiptPublic(BaseModel):
    products: List[Product]
    payment: Payment
    total: float
    rest: float
    created_at: datetime

    class Config:
        from_attributes = True


class ReceiptList(BaseModel):
    id: uuid.UUID
    created_at: datetime
    total: float
    payment_type: PaymentType

    class Config:
        from_attributes = True
