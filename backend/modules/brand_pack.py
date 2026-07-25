"""
LUIN Brand Pack Module — Vectorization & Palette Extraction
"""

import base64
import io
import logging
from typing import Optional

import numpy as np
from PIL import Image
from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

logger = logging.getLogger("luin.brand")
router = APIRouter()


class PaletteResult(BaseModel):
    primary: str
    secondary: str
    accent: str
    neutral: str
    total_colors: int


class VectorizeResult(BaseModel):
    svg_base64: str
    width: int
    height: int
    colors_detected: int


class BrandPackResponse(BaseModel):
    palette: PaletteResult
    svg_asset: Optional[str] = None
    logo_path: Optional[str] = None
    font_family: Optional[str] = None
    design_tokens: dict


def trace_to_svg(image: Image.Image, max_colors: int = 16) -> tuple:
    try:
        import vtracer
    except ImportError:
        return generate_simple_svg(image), 0
    img_array = np.array(image.convert("RGB"))
    result = vtracer.tracing(
        img_array, max_colors=max_colors, type="color", scale=1.0,
        simplify_tolerance=0.2, inner_simplify_tolerance=0.1,
        dot_order=4, corner_threshold=45.0,
    )
    return result.svg(), result.colors_count()


def generate_simple_svg(image: Image.Image) -> str:
    w, h = image.size
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="#e2e8f0"/><text x="{w//2}" y="{h//2}" text-anchor="middle" fill="#64748b" font-size="14">LUIN Brand Asset</text></svg>'


def extract_palette(image: Image.Image, k: int = 4) -> PaletteResult:
    img_array = np.array(image.convert("RGB"))
    pixels = img_array.reshape(-1, 3)
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(pixels)
    centers = kmeans.cluster_centers_
    labels = kmeans.labels_
    counts = np.bincount(labels)
    sorted_indices = np.argsort(-counts)

    def rgb_to_hex(rgb):
        return f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"

    return PaletteResult(
        primary=rgb_to_hex(centers[sorted_indices[0]]),
        secondary=rgb_to_hex(centers[sorted_indices[1]]),
        accent=rgb_to_hex(centers[sorted_indices[2]]),
        neutral=rgb_to_hex(centers[sorted_indices[3]]),
        total_colors=k,
    )


@router.post("/brand/vectorize", response_model=VectorizeResult)
async def vectorize_image(file: UploadFile):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files accepted.")
    image_data = await file.read()
    try:
        image = Image.open(io.BytesIO(image_data))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")
    svg_string, colors = trace_to_svg(image)
    svg_b64 = base64.b64encode(svg_string.encode()).decode()
    return VectorizeResult(svg_base64=svg_b64, width=image.width, height=image.height, colors_detected=colors)


@router.post("/brand/palette", response_model=PaletteResult)
async def extract_palette_route(file: UploadFile):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files accepted.")
    image_data = await file.read()
    try:
        image = Image.open(io.BytesIO(image_data))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")
    return extract_palette(image)


@router.post("/brand/generate-pack", response_model=BrandPackResponse)
async def generate_brand_pack(
    logo: Optional[UploadFile] = None,
    brand_colors: Optional[str] = None,
    font_family: Optional[str] = None,
):
    colors = brand_colors.split(",") if brand_colors else []
    palette = PaletteResult(
        primary=colors[0] if len(colors) > 0 else "#0f172a",
        secondary=colors[1] if len(colors) > 1 else "#1e293b",
        accent=colors[2] if len(colors) > 2 else "#3b82f6",
        neutral=colors[3] if len(colors) > 3 else "#64748b",
        total_colors=4,
    )
    return BrandPackResponse(
        palette=palette, svg_asset=None, logo_path=None,
        font_family=font_family or "Inter",
        design_tokens={
            "colors": {"primary": palette.primary, "secondary": palette.secondary, "accent": palette.accent, "neutral": palette.neutral},
            "typography": {"font_family": font_family or "Inter", "heading_weight": "700", "body_weight": "400"},
            "spacing": {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px"},
        },
    )
