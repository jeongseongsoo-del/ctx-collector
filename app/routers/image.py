from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from app.services.ctx_image import get_product_images


router = APIRouter()


@router.get("/ctx/images")
async def get_images(
    proino: str = Query(..., description="CTX 상품번호")
) -> Dict[str, Any]:

    try:
        images = await get_product_images(proino)

        return {
            "proino": proino,
            "images": images,
            "count": len(images),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"상품 이미지 조회 실패: {str(exc)}",
        ) from exc