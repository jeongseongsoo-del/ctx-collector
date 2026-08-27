from fastapi import FastAPI

from app.routers.health import router as health_router
from app.routers.item import router as item_router
from app.routers.product import router as product_router

app = FastAPI(title="CTX Collector API", version="1.0.0")

app.include_router(health_router)
app.include_router(item_router)
app.include_router(product_router)
