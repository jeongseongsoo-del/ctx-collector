import asyncio
import re
import time
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException
from playwright.sync_api import sync_playwright

from app.scraper import clean_html_for_detail_page, parse_spec_from_html, parse_table_trs

CTX_EBOOK_URL = "https://ctx.cretec.kr/CtxApp/ebook/selectEbookUninumSearch.do"
CTX_POWER_URL = "https://ctx.cretec.kr/CtxApp/ctx/selectPowerSearchJson.do"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://ctx.cretec.kr/",
}


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


def extract_delivery_table_html(page) -> str:
    if page.locator("#itemDtlTbl").count() == 0:
        return ""

    return page.evaluate(
        r"""
        () => {
            const root = document.querySelector('#itemDtlTbl');
            if (!root) return '';
            const tables = [...root.querySelectorAll('table')];
            for (const table of tables) {
                const text = (table.textContent || '').replace(/\s+/g, ' ').trim();
                if (/화물업체|택배|배송|운임|금액|대신택배|CJ택배/.test(text)) {
                    return table.outerHTML;
                }
            }
            return tables[0] ? tables[0].outerHTML : '';
        }
        """
    )


def extract_delivery_fallback(page) -> Dict[str, Any]:
    html = page.content()
    text = re.sub(r"\s+", " ", html)
    patterns = [
        r"화물업체\s*[:：]?\s*([^<]+?)\s*금액\s*[:：]?\s*([0-9,]+)",
        r"(대신택배|CJ택배|한진택배|롯데택배|로젠택배|우체국택배)\s*[:：]?\s*([0-9,]+)",
        r"(배송비|운임|택배비)\s*[:：]?\s*([0-9,]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            carrier = match.group(1).strip()
            amount = int(match.group(2).replace(",", ""))
            return {carrier: amount}

    return {}


def scrape_item_data(itemCd: str, compCd: Optional[str] = "C") -> Dict[str, Any]:
    url = f"https://ctx.cretec.kr/CtxApp/ctx/selectItemDtlIfrm.do?itemCd={itemCd}&compCd={compCd or ''}"
    playwright, browser = build_browser()

    try:
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.locator("#metaInfoTbl").wait_for(state="visible", timeout=15000)

        meta_html = page.locator("#metaInfoTbl").evaluate("(element) => element.outerHTML")
        deli_table = extract_delivery_table_html(page)
        delivery = parse_table_trs(deli_table) if deli_table else extract_delivery_fallback(page)

        detail_html = ""
        try:
            detail_html = page.locator("#itemDetailDiv").evaluate("(element) => element.outerHTML")
        except Exception:
            detail_html = ""

        spec = parse_spec_from_html(meta_html)
        if not delivery:
            delivery = extract_delivery_fallback(page)
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


def scrape_prod_data(prodCd: str) -> Dict[str, Any]:
    url = f"https://ctx.cretec.kr/CtxApp/ctx/ctx_ebook?prodCd={prodCd}"
    playwright, browser = build_browser()

    try:
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        meta_html = ""
        try:
            page.locator("#metaInfoTbl").wait_for(state="visible", timeout=15000)
            meta_html = page.locator("#metaInfoTbl").evaluate("(element) => element.outerHTML")
        except Exception:
            meta_html = page.locator("body").evaluate("(element) => element.outerHTML")

        deli_table = extract_delivery_table_html(page)
        delivery = parse_table_trs(deli_table) if deli_table else extract_delivery_fallback(page)

        detail_html = ""
        try:
            detail_html = page.locator("#itemDetailDiv").evaluate("(element) => element.outerHTML")
        except Exception:
            try:
                detail_html = page.locator("#prodDetailDiv").evaluate("(element) => element.outerHTML")
            except Exception:
                detail_html = page.locator("body").evaluate("(element) => element.outerHTML")

        spec = parse_spec_from_html(meta_html) if meta_html else {}
        if not delivery:
            delivery = extract_delivery_fallback(page)
        detail = clean_html_for_detail_page(detail_html) if detail_html else ""

        return {
            "prodCd": prodCd,
            "url": url,
            "spec": spec,
            "delivery": delivery,
            "detail": detail,
        }
    finally:
        browser.close()
        playwright.stop()


async def get_product_data(prodCd: str) -> Dict[str, Any]:
    timestamp = str(int(time.time() * 1000))
    ebook_params = {"prodCd": prodCd, "itemCd": "", "_": timestamp}
    power_params = {"prod_cd": prodCd, "keyword": "", "_": timestamp}

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            ebook_response, power_response = await asyncio.gather(
                client.get(CTX_EBOOK_URL, params=ebook_params, headers=HEADERS),
                client.get(CTX_POWER_URL, params=power_params, headers=HEADERS),
            )

        ebook_response.raise_for_status()
        power_response.raise_for_status()

        ebook_data = ebook_response.json()
        power_data = power_response.json()

        ebook_result = ebook_data.get("result", [])
        if not ebook_result:
            raise HTTPException(status_code=404, detail=f"Ebook 상품을 찾을 수 없습니다: {prodCd}")

        ebook_item = ebook_result[0]
        ebook_fields = [
            "procode",
            "proino",
            "procpn",
            "cateNm",
            "proinm",
            "prostd",
            "promod",
            "pconam",
            "linkX1",
            "linkY1",
            "linkX2",
            "linkY2",
            "mastDb",
            "folder",
            "pg",
        ]
        ebook_result_data = {key: ebook_item.get(key) for key in ebook_fields}

        power_result = power_data.get("result", {})
        power_items = power_result.get("items", [])
        if not power_items:
            raise HTTPException(status_code=404, detail=f"Power 상품을 찾을 수 없습니다: {prodCd}")

        power_item = power_items[0]
        qties = (power_item.get("qties") or "").split(",")
        moq = qties[0] if len(qties) > 0 else ""
        unit = qties[3] if len(qties) > 3 else ""

        power_fields = [
            "qties",
            "std_sale_pric",
            "std_unit_pric",
            "sale_prices",
            "std_unit_pric_rte",
            "item_stdz",
            "img_file",
            "image_name",
            "d1sum",
            "s1sum",
            "order_qty",
            "ebook_yn",
            "item_use_cd",
            "stpay",
            "recp_expt_dt",
            "recp_expt_dt_s1",
            "dept_info",
            "dept_info_s1",
            "ritteryn",
            "imp_cargo_serv",
            "cg_psvc_yn",
            "no_sale_item_yn",
            "modl_no",
            "yusa",
            "brnd_cd",
            "rtn_imps_yn",
            "imp_delv_serv",
            "imp_delv_serv_all",
            "no_air_trans_yn",
            "hand_with_care_yn",
            "delv_pay_item_cls_cd",
            "online_no_sale",
            "direct_no_sale_yn",
            "chemi_yn",
            "as_cost_yn",
            "oil_remove_yn",
            "indi_cargo_yn",
            "rcmd_cls",
        ]

        power_result_data = {key: power_item.get(key) for key in power_fields}
        power_result_data["moq"] = moq
        power_result_data["unit"] = unit
        return {**ebook_result_data, **power_result_data}

    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="CTX 서버 응답 시간 초과") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"CTX 서버 HTTP 오류: {exc.response.status_code}",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"데이터 수집 오류: {str(exc)}") from exc
