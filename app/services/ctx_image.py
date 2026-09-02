from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx
from lxml import html


CTX_PRODUCT_IMAGE_API_URL = "https://ctx.cretec.kr/CtxApp/com/imgView.do"


def extract_product_images(content: str, base_url: str) -> list[str]:
    document = html.fromstring(content)

    # CTX 상품 이미지 영역
    image_elements = document.xpath(
        "//*[contains(concat(' ', normalize-space(@class), ' '), ' mutl-img-div ')]//img"
    )

    # 이미지 영역을 찾지 못하면 전체 이미지 검색
    if not image_elements:
        image_elements = document.xpath("//img[@data-zoom or @src]")

    images = []

    for image in image_elements:
        source = image.get("data-zoom") or image.get("src")

        if not source:
            continue

        image_url = urljoin(base_url, source)

        # query string 제거
        parsed_url = urlsplit(image_url)

        image_url = urlunsplit(
            (
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                "",
                "",
            )
        )

        # 중복 제거
        if image_url not in images:
            images.append(image_url)

    return images


async def get_product_images(proino: str) -> list[str]:
    if not proino:
        return []

    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=True,
    ) as client:

        response = await client.get(
            CTX_PRODUCT_IMAGE_API_URL,
            params={
                "path": "/resource",
                "itemCd": proino,
                "detailYn": "Y",
                "zoomViewYn": "N",
            },
        )

        response.raise_for_status()

        return extract_product_images(
            response.text,
            str(response.url),
        )