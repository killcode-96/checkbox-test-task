from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import models
from app.schemas import receipt as receipt_schemas
from app.database.models import ShortLink
from datetime import date
from sqlalchemy import and_, select
import uuid


class ReceiptService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_receipt(
        self, receipt: receipt_schemas.ReceiptCreate, user_id: uuid.UUID
    ) -> models.Receipt:
        """Creates a new receipt."""
        products = [
            models.Product(name=p.name, price=p.price, quantity=p.quantity)
            for p in receipt.products
        ]

        total = sum(product.price * product.quantity for product in products)

        db_receipt = models.Receipt(
            user_id=user_id,
            products=products,
            payment_type=receipt.payment.type,
            payment_amount=receipt.payment.amount,
            total=total,
            rest=(
                (payment_amount - total)
                if (payment_amount := receipt.payment.amount)
                else 0
            ),
        )

        self.db.add(db_receipt)
        await self.db.commit()
        await self.db.refresh(db_receipt)

        short_link = await ShortLink.create_short_link(
            db=self.db, receipt_id=db_receipt.id
        )
        db_receipt.short_link = short_link

        await self.db.refresh(db_receipt, attribute_names=["short_link", "products"])

        return db_receipt

    async def get_receipt(
        self, receipt_id: uuid.UUID, user_id: uuid.UUID
    ) -> models.Receipt | None:
        """Retrieves a receipt by ID for a specific user with eager loading."""
        query = (
            select(models.Receipt)
            .where(
                and_(models.Receipt.user_id == user_id, models.Receipt.id == receipt_id)
            )
            .options(selectinload(models.Receipt.products))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_receipts(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 10,
        start_date: date | None = None,
        end_date: date | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        payment_type: receipt_schemas.PaymentType | None = None,
    ) -> Sequence[models.Receipt]:
        """Retrieves a list of receipts for a user, with pagination and filters."""
        query = (
            select(models.Receipt)
            .where(models.Receipt.user_id == user_id)
            .options(
                selectinload(models.Receipt.products),
            )
        )

        if start_date:
            query = query.where(models.Receipt.created_at >= start_date)
        if end_date:
            query = query.where(models.Receipt.created_at <= end_date)
        if min_amount:
            query = query.where(models.Receipt.total >= min_amount)
        if max_amount:
            query = query.where(models.Receipt.total <= max_amount)
        if payment_type:
            query = query.where(models.Receipt.payment_type == payment_type)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_receipt_by_short_code(self, short_code: str) -> models.Receipt | None:
        """Retrieves a receipt by short code."""
        query = (
            select(models.Receipt)
            .join(models.Receipt.short_link)
            .where(models.ShortLink.short_code == short_code)
            .options(selectinload(models.Receipt.products))
        )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()
