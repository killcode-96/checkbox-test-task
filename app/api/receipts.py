import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import db, models
from app.schemas import receipt as receipt_schemas
from app.api.users import get_current_user
from typing import List, Annotated
from datetime import date
from app.core.config import settings

from app.services.receipt import ReceiptService

router = APIRouter()


def get_receipt_service(db: AsyncSession = Depends(db.get_db)) -> ReceiptService:
    return ReceiptService(db)


def generate_public_url(short_code: str, prefix: str = "public") -> str:
    return f"http://{settings.HOST}/{prefix}/{short_code}"


@router.post(
    "/",
    response_model=receipt_schemas.Receipt,
    summary="Створення чеку",
    description="Створює новий чек для аутентифікованого користувача.",
)
async def create_receipt(
    receipt: receipt_schemas.ReceiptCreate,
    current_user: models.User = Depends(get_current_user),
    receipt_service: ReceiptService = Depends(get_receipt_service),
):
    db_receipt = await receipt_service.create_receipt(
        receipt=receipt, user_id=current_user.id
    )

    return receipt_schemas.Receipt(
        id=db_receipt.id,
        products=[
            receipt_schemas.Product(
                name=p.name,
                price=p.price,
                quantity=p.quantity,
                total=p.price * p.quantity,
            )
            for p in db_receipt.products
        ],
        payment=receipt_schemas.Payment(
            type=db_receipt.payment_type,
            amount=db_receipt.payment_amount,
        ),
        total=db_receipt.total,
        rest=db_receipt.rest,
        user_id=db_receipt.user_id,
        public_url=generate_public_url(db_receipt.short_link.short_code),
        created_at=db_receipt.created_at,
    )


@router.get(
    "/",
    response_model=List[receipt_schemas.Receipt],
    summary="Отримати список чеків",
    description="Повертає список чеків для аутентифікованого користувача з можливістю фільтрації та пагінації.",
)
async def list_receipts(
    current_user: models.User = Depends(get_current_user),
    receipt_service: ReceiptService = Depends(get_receipt_service),
    skip: int = Query(0, description="Кількість елементів для пропуску при пагінації"),
    limit: int = Query(10, description="Кількість елементів на сторінці"),
    start_date: Annotated[
        date | None,
        Query(description="Початкова дата для фільтрації (YYYY-MM-DD)"),
    ] = None,
    end_date: Annotated[
        date | None, Query(description="Кінцева дата для фільтрації (YYYY-MM-DD)")
    ] = None,
    min_amount: Annotated[
        float | None, Query(description="Мінімальна загальна сума для фільтрації")
    ] = None,
    max_amount: Annotated[
        float | None, Query(description="Максимальна загальна сума для фільтрації")
    ] = None,
    payment_type: Annotated[
        receipt_schemas.PaymentType | None,
        Query(description="Тип платежу для фільтрації"),
    ] = None,
):
    receipts = await receipt_service.list_receipts(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        payment_type=payment_type,
    )

    response = []
    for receipt in receipts:
        response.append(
            receipt_schemas.Receipt(
                id=receipt.id,
                products=[
                    receipt_schemas.Product(
                        name=p.name,
                        price=p.price,
                        quantity=p.quantity,
                        total=p.price * p.quantity,
                    )
                    for p in receipt.products
                ],
                payment=receipt_schemas.Payment(
                    type=receipt.payment_type,
                    amount=receipt.payment_amount,
                ),
                total=receipt.total,
                rest=receipt.rest,
                user_id=receipt.user_id,
                public_url=generate_public_url(receipt.short_link.short_code),
                created_at=receipt.created_at,
            )
        )
    return response


@router.get(
    "/{receipt_id}",
    response_model=receipt_schemas.Receipt,
    summary="Отримати чек",
    description="Повертає конкретний чек за його ID для аутентифікованого користувача.",
)
async def get_receipt(
    receipt_id: Annotated[uuid.UUID, Path(title="The ID of the receipt to retrieve")],
    current_user: models.User = Depends(get_current_user),
    receipt_service: ReceiptService = Depends(get_receipt_service),
):
    receipt = await receipt_service.get_receipt(
        receipt_id=receipt_id, user_id=current_user.id
    )
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found"
        )

    return receipt_schemas.Receipt(
        id=receipt.id,
        products=[
            receipt_schemas.Product(
                name=p.name,
                price=p.price,
                quantity=p.quantity,
                total=p.price * p.quantity,
            )
            for p in receipt.products
        ],
        payment=receipt_schemas.Payment(
            type=receipt.payment_type,
            amount=receipt.payment_amount,
        ),
        total=receipt.total,
        rest=receipt.rest,
        user_id=receipt.user_id,
        public_url=generate_public_url(receipt.short_link.short_code),
        created_at=receipt.created_at,
    )
