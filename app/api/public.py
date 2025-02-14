from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import PlainTextResponse

from app.database import db
from app.core.config import settings
from app.services.receipt import ReceiptService
from app.services.public import format_receipt_text

router = APIRouter()


def get_receipt_service(db: AsyncSession = Depends(db.get_db)) -> ReceiptService:
    return ReceiptService(db)


@router.get(
    "/{short_code}/",
    response_class=PlainTextResponse,
    summary="Отримати чек по короткому коду.",
    description="Отримати чек по короткому коду (публічний доступ - авторизація не потрібна).",
)
async def get_receipt_public(
    short_code: str, receipt_service: ReceiptService = Depends(get_receipt_service)
):
    receipt = await receipt_service.get_receipt_by_short_code(short_code)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return format_receipt_text(receipt, settings.LINE_LENGTH)
