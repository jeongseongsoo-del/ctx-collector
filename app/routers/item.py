from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.ctx_scraper import scrape_item_data

router = APIRouter()


class ScrapeItemRequest(BaseModel):
    item_cd: str = Field(..., description="상품 코드")
    comp_cd: Optional[str] = Field(default="C", description="회사 코드")


@router.get("/scrape-item")
def scrape_item(
    itemCd: str = Query(..., alias="itemCd"),
    compCd: Optional[str] = Query(default="C", alias="compCd"),
) -> Dict[str, Any]:
    try:
        return scrape_item_data(itemCd=itemCd, compCd=compCd)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"scrape failed: {str(exc)}") from exc


@router.post("/scrape-item")
def scrape_item_post(payload: ScrapeItemRequest) -> Dict[str, Any]:
    return scrape_item(itemCd=payload.item_cd, compCd=payload.comp_cd)
