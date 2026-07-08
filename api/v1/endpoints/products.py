from fastapi import APIRouter, Depends
from database import get_db, Base
from pydantic import BaseModel, Field, ConfigDict
from utils import utils
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String

products_router = APIRouter()
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)

class ProductCreate(BaseModel):
    name: str
    price: int = Field(gt=0)
    model_config = ConfigDict(from_attributes=True)

class ProductUpdate(BaseModel):
    name: str | None = None
    price: int | None = Field(default=None, gt=0)


@products_router.post("/products")
def create_product(product: ProductCreate, db:Session = Depends(get_db)):
    new_product = Product(name = product.name, price = product.price)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@products_router.get("/products/{id}")
def get_product(id, db:Session = Depends(get_db)):
   product = db.query(Product).filter(Product.id == id).first()
   return product

@products_router.get("/products")
def get_products(db:Session = Depends(get_db)):
   product = db.query(Product).all()
   return product

@products_router.put("/products")
def update_products(id: str, product_data: ProductUpdate, db:Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()  

    if product_data.name is not None:
        product.name = product_data.name
    if product_data.price is not None:
        product.price = product_data.price
    db.commit()
    db.refresh(product)
    return product


@products_router.delete("/products/{id}")
def delete_product(id: int, db:Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()  
    db.delete(product)
    db.commit()
    return id