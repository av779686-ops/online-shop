from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import Session

from database import Base, get_db
from api.v1.endpoints.auth import User
from api.v1.endpoints.products import Product
from utils.utils import decode_token, is_able_pay

basket_router = APIRouter(prefix="/basket", tags=["Basket"])

class Basket(Base):
    __tablename__ = "baskets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

class BasketItem(Base):
    __tablename__ = "basket_items"
    id = Column(Integer, primary_key=True)
    basket_id = Column(Integer, ForeignKey("baskets.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    qty = Column(Integer, nullable=False)

class BasketLine(BaseModel):
    product_id: int
    qty: int = Field(gt=0, le=99)

def current_user(request: Request, db: Session):
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(401, "Authentication required")
    payload = decode_token(auth.split(" ", 1)[1])
    user = db.query(User).filter(User.id == int(payload.get("sub", 0))).first() if payload else None
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user

def get_basket(user, db):
    basket = db.query(Basket).filter(Basket.user_id == user.id).first()
    if not basket:
        basket = Basket(user_id=user.id)
        db.add(basket); db.commit(); db.refresh(basket)
    return basket

def serialize(basket, db):
    lines = []
    total = 0
    for item in db.query(BasketItem).filter(BasketItem.basket_id == basket.id).all():
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            line_total = product.price * item.qty; total += line_total
            lines.append({"product_id": product.id, "name": product.name, "price": product.price, "qty": item.qty, "line_total": line_total, "image": None})
    return {"items": lines, "total": total}

@basket_router.get("")
def read_basket(request: Request, db: Session = Depends(get_db)):
    return serialize(get_basket(current_user(request, db), db), db)

@basket_router.post("/items")
def add_item(line: BasketLine, request: Request, db: Session = Depends(get_db)):
    basket = get_basket(current_user(request, db), db)
    if not db.query(Product).filter(Product.id == line.product_id).first(): raise HTTPException(404, "Product not found")
    item = db.query(BasketItem).filter(BasketItem.basket_id == basket.id, BasketItem.product_id == line.product_id).first()
    if item: item.qty = line.qty
    else: db.add(BasketItem(basket_id=basket.id, product_id=line.product_id, qty=line.qty))
    db.commit(); return serialize(basket, db)

@basket_router.delete("/items/{product_id}")
def remove_item(product_id: int, request: Request, db: Session = Depends(get_db)):
    basket = get_basket(current_user(request, db), db)
    item = db.query(BasketItem).filter(BasketItem.basket_id == basket.id, BasketItem.product_id == product_id).first()
    if item: db.delete(item); db.commit()
    return serialize(basket, db)

@basket_router.post("/checkout")
def checkout(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db); basket = get_basket(user, db)
    items = db.query(BasketItem).filter(BasketItem.basket_id == basket.id).all()
    priced = [type("Line", (), {"price": db.query(Product).filter(Product.id == i.product_id).first().price, "qty": i.qty}) for i in items]
    if not is_able_pay(priced, user.money): raise HTTPException(400, "Insufficient balance")
    total = sum(x.price * x.qty for x in priced); user.money -= total
    for item in items: db.delete(item)
    db.commit(); return {"message": "Purchase completed", "total": total, "money": user.money}
