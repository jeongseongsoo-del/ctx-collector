import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from playwright.sync_api import sync_playwright
from pydantic import BaseModel, Field

from app.scraper import clean_html_for_detail_page, parse_spec_from_html, parse_table_trs

app = FastAPI(title="CTX Collector API", version="1.0.0")


class ScrapeItemRequest(BaseModel):
    item_cd: str = Field(..., description="상품 코드")
    comp_cd: Optional[str] = Field(default="C", description="회사 코드")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def build_browser():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-extensions",
        ],
    )
    return playwright, browser


@app.get("/scrape-item")
def scrape_item(
    itemCd: str = Query(..., alias="itemCd"),
    compCd: Optional[str] = Query(default="C", alias="compCd"),
) -> Dict[str, Any]:
    try:
        url = f"https://ctx.cretec.kr/CtxApp/ctx/selectItemDtlIfrm.do?itemCd={itemCd}&compCd={compCd or ''}"

        playwright, browser = build_browser()

        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto(url, wait_until="load", timeout=60000)
            page.locator("#metaInfoTbl").wait_for(state="visible", timeout=30000)

            meta_html = page.locator("#metaInfoTbl").evaluate("(element) => element.outerHTML")

            deli_table = ""
            try:
                deli_table = page.locator('//*[@id="itemDtlTbl"]/tbody/tr[10]/td/table').evaluate(
                    "(element) => element.outerHTML"
                )
            except Exception:
                deli_table = ""

            detail_html = ""
            try:
                detail_html = page.locator("#itemDetailDiv").evaluate("(element) => element.outerHTML")
            except Exception:
                detail_html = ""

            spec = parse_spec_from_html(meta_html)
            delivery = parse_table_trs(deli_table) if deli_table else {}
            detail = clean_html_for_detail_page(detail_html) if detail_html else ""

            return {
                "itemCd": itemCd,
                "compCd": compCd or "",
                "url": url,
                "spec": spec,
                "delivery": delivery,
                "detail": detail,
            }
        finally:
            browser.close()
            playwright.stop()
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"scrape failed: {str(exc)}") from exc


@app.post("/scrape-item")
def scrape_item_post(payload: ScrapeItemRequest) -> Dict[str, Any]:
    return scrape_item(itemCd=payload.item_cd, compCd=payload.comp_cd)
