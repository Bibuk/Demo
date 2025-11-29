from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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

class ProductCreate(BaseModel):
    name: str
    price: float
    description: str
    image: str
    category: str

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    old_price: Optional[float] = None
    description: Optional[str] = None
    image: Optional[str] = None
    category: Optional[str] = None

class DiscountApply(BaseModel):
    discount_percent: float

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

# Endpoints для управления товарами (для техподдержки)

@router.post("/products")
async def create_product(product: ProductCreate):
    """Создание нового товара (только для техподдержки)"""
    new_id = max(p["id"] for p in products_db) + 1 if products_db else 1
    
    new_product = {
        "id": new_id,
        "name": product.name,
        "price": product.price,
        "old_price": None,
        "description": product.description,
        "image": product.image,
        "category": product.category
    }
    
    products_db.append(new_product)
    
    return {
        "success": True,
        "message": "Товар успешно создан",
        "product": new_product
    }

@router.put("/products/{product_id}")
async def update_product(product_id: int, product_update: ProductUpdate):
    """Обновление товара (только для техподдержки)"""
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    update_data = product_update.dict(exclude_unset=True)
    product.update(update_data)
    
    return {
        "success": True,
        "message": "Товар успешно обновлен",
        "product": product
    }

@router.delete("/products/{product_id}")
async def delete_product(product_id: int):
    """Удаление товара (только для техподдержки)"""
    global products_db
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    products_db = [p for p in products_db if p["id"] != product_id]
    
    return {
        "success": True,
        "message": "Товар успешно удален"
    }

@router.post("/products/{product_id}/discount")
async def apply_discount(product_id: int, discount: DiscountApply):
    """Применение скидки к товару (только для техподдержки)"""
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    if discount.discount_percent < 0 or discount.discount_percent > 100:
        raise HTTPException(status_code=400, detail="Скидка должна быть от 0 до 100%")
    
    # Сохраняем старую цену, если ее еще нет
    if product["old_price"] is None:
        product["old_price"] = product["price"]
    
    # Вычисляем новую цену со скидкой
    original_price = product["old_price"] if product["old_price"] else product["price"]
    new_price = original_price * (1 - discount.discount_percent / 100)
    product["price"] = round(new_price, 2)
    
    return {
        "success": True,
        "message": f"Скидка {discount.discount_percent}% применена",
        "product": product
    }

@router.delete("/products/{product_id}/discount")
async def remove_discount(product_id: int):
    """Удаление скидки с товара (только для техподдержки)"""
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    if product["old_price"] is not None:
        product["price"] = product["old_price"]
        product["old_price"] = None
    
    return {
        "success": True,
        "message": "Скидка удалена",
        "product": product
    }
