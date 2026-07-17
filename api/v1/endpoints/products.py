from fastapi import APIRouter, Depends, Request, HTTPException
from database import get_db, Base
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, LargeBinary
from utils.utils import decode_token
import base64

products_router = APIRouter()
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
    try:
        encoded = value.split(",", 1)[1] if "," in value else value
        return base64.b64decode(encoded)
    except (ValueError, TypeError):
        raise HTTPException(422, "Image must be a valid base64 data URL")

def product_json(product):
    image = None
    if product.image:
        raw = bytes(product.image)
        mime = "image/png" if raw.startswith(b"\x89PNG") else "image/gif" if raw.startswith(b"GIF") else "image/webp" if raw.startswith(b"RIFF") else "image/jpeg"
        image = f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")
    return {"id": product.id, "name": product.name, "price": product.price, "image": image}

def require_admin(request: Request, db: Session):
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authentication required")
    payload = decode_token(authorization.split(" ", 1)[1])
    if not payload or not payload.get("sub"):
        raise HTTPException(401, "Invalid or expired token")
    from .auth import User
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or user.role.value != "admin":
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
