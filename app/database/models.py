import uuid
import secrets
import string

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)

    receipts = relationship("Receipt", back_populates="user")


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    payment_type = Column(
        Enum("cash", "cashless", name="payment_type_enum"), nullable=False
    )
    payment_amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="receipts")
    products = relationship("Product", back_populates="receipt")
    short_link = relationship("ShortLink", back_populates="receipt", uselist=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("receipts.id"))
    name = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)

    receipt = relationship("Receipt", back_populates="products")


class ShortLink(Base):
    __tablename__ = "short_links"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(
        UUID(as_uuid=True), ForeignKey("receipts.id"), unique=True, nullable=False
    )
    short_code = Column(String, unique=True, nullable=False, index=True)

    receipt = relationship("Receipt", back_populates="short_link")  # Змінено

    @staticmethod
    def generate_short_code(length: int = 8) -> str:
        """Generates a random short code."""
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @classmethod
    def create_short_link(cls, db: "Session", receipt_id: UUID) -> "ShortLink":  # type: ignore
        """Creates a short link for a receipt."""
        while True:
            short_code = cls.generate_short_code()
            existing_link = db.query(cls).filter(cls.short_code == short_code).first()
            if not existing_link:
                break

        short_link = cls(receipt_id=receipt_id, short_code=short_code)
        db.add(short_link)
        db.commit()
        db.refresh(short_link)
        return short_link
