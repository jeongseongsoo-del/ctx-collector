from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.ctx_scraper import get_product_data, scrape_prod_data

router = APIRouter()


class ScrapeProdRequest(BaseModel):
    prod_cd: str = Field(..., description="전자책/상품 코드")


@router.get("/ctx/product")
async def get_product(
    prodCd: str = Query(..., description="CTX 상품번호")
) -> Dict[str, Any]:
    return await get_product_data(prodCd)


@router.get("/scrape-prod")
def scrape_prod(
    prodCd: str = Query(..., alias="prodCd"),
) -> Dict[str, Any]:
    try:
        return scrape_prod_data(prodCd)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"scrape failed: {str(exc)}") from exc


@router.post("/scrape-prod")
def scrape_prod_post(payload: ScrapeProdRequest) -> Dict[str, Any]:
    return scrape_prod(prodCd=payload.prod_cd)
