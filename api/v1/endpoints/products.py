import base64
import binascii
from fastapi import APIRouter, Depends, Request, HTTPException
from database import get_db, Base
from logging_config import logger
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, LargeBinary
from utils.utils import decode_token

products_router = APIRouter()

ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png"}
JPEG_SIGNATURE = b"\xff\xd8\xff"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)
    image = Column(LargeBinary, nullable=True)

class ProductCreate(BaseModel):
    name: str
    price: int = Field(gt=0)
    image: str | None = None
    model_config = ConfigDict(from_attributes=True)

class ProductUpdate(BaseModel):
    name: str | None = None
    price: int | None = Field(default=None, gt=0)
    image: str | None = None

def image_bytes(value):
    if not value:
        return None

    declared_mime = None
    encoded = value
    if value.startswith("data:"):
        try:
            metadata, encoded = value.split(",", 1)
        except ValueError:
            logger.warning("Rejected malformed image data URL")
            raise HTTPException(422, "Image must be a valid JPG or PNG")

        parts = metadata[5:].lower().split(";")
        declared_mime = parts[0]
        if declared_mime not in ALLOWED_IMAGE_MIME_TYPES or "base64" not in parts[1:]:
            logger.warning("Rejected unsupported image type: %s", declared_mime)
            raise HTTPException(422, "Only JPG and PNG images are allowed")

    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError, TypeError):
        logger.warning("Rejected invalid base64 image")
        raise HTTPException(422, "Image must be a valid base64-encoded JPG or PNG")

    actual_mime = image_mime(raw)
    if actual_mime is None:
        logger.warning("Rejected image with an unsupported file signature")
        raise HTTPException(422, "Only JPG and PNG images are allowed")
    if declared_mime and (
        declared_mime == "image/png"
    ) != (
        actual_mime == "image/png"
    ):
        logger.warning(
            "Rejected image whose declared type %s does not match its content",
            declared_mime,
        )
        raise HTTPException(422, "Image type does not match its content")

    return raw


def image_mime(raw):
    if raw.startswith(PNG_SIGNATURE):
        return "image/png"
    if raw.startswith(JPEG_SIGNATURE):
        return "image/jpeg"
    return None

def product_json(product):
    image = None
    if product.image:
        raw = bytes(product.image)
        mime = image_mime(raw)
        if mime:
            image = f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")
    return {"id": product.id, "name": product.name, "price": product.price, "image": image}

def require_admin(request: Request, db: Session):
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        logger.warning("Product administration rejected: authentication required")
        raise HTTPException(401, "Authentication required")
    payload = decode_token(authorization.split(" ", 1)[1])
    if not payload or not payload.get("sub"):
        logger.warning("Product administration rejected: invalid or expired token")
        raise HTTPException(401, "Invalid or expired token")
    from .auth import User
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or user.role.value != "admin":
        logger.warning("Product administration rejected: admin access required")
        raise HTTPException(403, "Admin access required")
    return user


@products_router.post("/products")
def create_product(product: ProductCreate, request: Request, db:Session = Depends(get_db)):
    require_admin(request, db)
    new_product = Product(name=product.name, price=product.price, image=image_bytes(product.image))
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return product_json(new_product)

@products_router.get("/products/{id}")
def get_product(id, db:Session = Depends(get_db)):
   product = db.query(Product).filter(Product.id == id).first()
   return product_json(product) if product else None

@products_router.get("/products")
def get_products(db:Session = Depends(get_db)):
   product = db.query(Product).all()
   return [product_json(item) for item in product]

@products_router.put("/products")
def update_products(id: str, product_data: ProductUpdate, request: Request, db:Session = Depends(get_db)):
    require_admin(request, db)
    product = db.query(Product).filter(Product.id == id).first()  
    if not product:
        raise HTTPException(404, "Product not found")

    if product_data.name is not None:
        product.name = product_data.name
    if product_data.price is not None:
        product.price = product_data.price
    if product_data.image is not None:
        product.image = image_bytes(product_data.image)
    db.commit()
    db.refresh(product)
    return product_json(product)


@products_router.delete("/products/{id}")
def delete_product(id: int, request: Request, db:Session = Depends(get_db)):
    require_admin(request, db)
    product = db.query(Product).filter(Product.id == id).first()  
    if not product:
        raise HTTPException(404, "Product not found")
    db.delete(product)
    db.commit()
    return id
