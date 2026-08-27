import json
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.scraper import clean_html_for_detail_page, parse_spec_from_html, parse_table_trs

app = FastAPI(title="CTX Collector API", version="1.0.0")


class ScrapeItemRequest(BaseModel):
    item_cd: str = Field(..., description="상품 코드")
    comp_cd: Optional[str] = Field(default="C", description="회사 코드")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def build_driver() -> webdriver.Chrome:
    chrome_bin = os.environ.get("CHROME_BIN") or "/usr/bin/chromium"
    driver_path = os.environ.get("CHROMEDRIVER_BIN") or "/usr/bin/chromedriver"

    options = Options()
    if os.path.exists(chrome_bin):
        options.binary_location = chrome_bin

    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--remote-debugging-port=9222")

    service = Service(executable_path=driver_path) if os.path.exists(driver_path) else Service()
    return webdriver.Chrome(service=service, options=options)


@app.get("/scrape-item")
def scrape_item(
    itemCd: str = Query(..., alias="itemCd"),
    compCd: Optional[str] = Query(default="C", alias="compCd"),
) -> Dict[str, Any]:
    try:
        url = f"https://ctx.cretec.kr/CtxApp/ctx/selectItemDtlIfrm.do?itemCd={itemCd}&compCd={compCd or ''}"

        driver = build_driver()

        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "metaInfoTbl"))
            )

            meta_html = driver.find_element(By.ID, "metaInfoTbl").get_attribute("outerHTML")

            deli_table = ""
            try:
                deli_table = driver.find_element(
                    By.XPATH,
                    '//*[@id="itemDtlTbl"]/tbody/tr[10]/td/table'
                ).get_attribute("outerHTML")
            except Exception:
                deli_table = ""

            detail_html = ""
            try:
                detail_html = driver.find_element(By.ID, "itemDetailDiv").get_attribute("outerHTML")
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
            driver.quit()
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"scrape failed: {str(exc)}") from exc


@app.post("/scrape-item")
def scrape_item_post(payload: ScrapeItemRequest) -> Dict[str, Any]:
    return scrape_item(itemCd=payload.item_cd, compCd=payload.comp_cd)
