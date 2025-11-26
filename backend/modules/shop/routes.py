from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/shop", tags=["Магазин"])

class Product(BaseModel):
    id: int
    name: str
    price: float
    old_price: Optional[float] = None
    description: str
    image: str
    category: str

class CartItem(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[CartItem]
    total: float
    customer_name: str
    customer_email: str
    customer_phone: str

products_db = [
    {
        "id": 1,
        "name": "Смартфон XYZ",
        "price": 25000,
        "old_price": 30000,
        "description": "Современный смартфон с отличными характеристиками",
        "image": "mobile",
        "category": "Электроника"
    },
    {
        "id": 2,
        "name": "Ноутбук ABC",
        "price": 65000,
        "old_price": None,
        "description": "Мощный ноутбук для работы и развлечений",
        "image": "laptop",
        "category": "Компьютеры"
    },
    {
        "id": 3,
        "name": "Наушники Pro",
        "price": 8500,
        "old_price": None,
        "description": "Беспроводные наушники с шумоподавлением",
        "image": "headphones",
        "category": "Аксессуары"
    },
    {
        "id": 4,
        "name": "Смарт-часы",
        "price": 12000,
        "old_price": 15000,
        "description": "Умные часы с множеством функций",
        "image": "watch",
        "category": "Аксессуары"
    },
    {
        "id": 5,
        "name": "Камера Digital",
        "price": 85000,
        "old_price": None,
        "description": "Профессиональная цифровая камера",
        "image": "camera",
        "category": "Фото"
    },
    {
        "id": 6,
        "name": "Мышка Gaming",
        "price": 3500,
        "old_price": None,
        "description": "Игровая мышь с RGB подсветкой",
        "image": "mouse",
        "category": "Аксессуары"
    }
]

carts_db = {}

@router.get("/products")
async def get_products(category: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None):
    filtered_products = products_db
    
    if category:
        filtered_products = [p for p in filtered_products if p["category"] == category]
    
    if min_price:
        filtered_products = [p for p in filtered_products if p["price"] >= min_price]
    
    if max_price:
        filtered_products = [p for p in filtered_products if p["price"] <= max_price]
    
    return {
        "success": True,
        "products": filtered_products,
        "total": len(filtered_products)
    }

@router.get("/products/{product_id}")
async def get_product(product_id: int):
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    return {
        "success": True,
        "product": product
    }

@router.get("/categories")
async def get_categories():
    categories = list(set(p["category"] for p in products_db))
    return {
        "success": True,
        "categories": categories
    }

@router.post("/cart/add")
async def add_to_cart(user_id: str, item: CartItem):
    if user_id not in carts_db:
        carts_db[user_id] = []
    
    product = next((p for p in products_db if p["id"] == item.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    cart = carts_db[user_id]
    existing_item = next((i for i in cart if i["product_id"] == item.product_id), None)
    
    if existing_item:
        existing_item["quantity"] += item.quantity
    else:
        cart.append(item.dict())
    
    return {
        "success": True,
        "message": "Товар добавлен в корзину",
        "cart_count": len(cart)
    }

@router.get("/cart/{user_id}")
async def get_cart(user_id: str):
    cart = carts_db.get(user_id, [])
    cart_items = []
    total = 0
    
    for item in cart:
        product = next((p for p in products_db if p["id"] == item["product_id"]), None)
        if product:
            item_total = product["price"] * item["quantity"]
            cart_items.append({
                **item,
                "product": product,
                "item_total": item_total
            })
            total += item_total
    
    return {
        "success": True,
        "items": cart_items,
        "total": total,
        "count": len(cart_items)
    }

@router.delete("/cart/{user_id}/{product_id}")
async def remove_from_cart(user_id: str, product_id: int):
    if user_id not in carts_db:
        raise HTTPException(status_code=404, detail="Корзина не найдена")
    
    cart = carts_db[user_id]
    carts_db[user_id] = [item for item in cart if item["product_id"] != product_id]
    
    return {
        "success": True,
        "message": "Товар удален из корзины"
    }

@router.post("/orders")
async def create_order(order: OrderCreate):
    order_id = 1000 + len(carts_db)
    
    return {
        "success": True,
        "message": "Заказ успешно оформлен",
        "order_id": order_id,
        "total": order.total
    }
