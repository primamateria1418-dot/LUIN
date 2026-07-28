"""
LUIN Ad-Hoc Generation API — Multi-modal generation sandbox
"""

import io
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.config import get_settings
from backend.database import Client, get_db

logger = logging.getLogger("luin.generate")
router = APIRouter()
settings = get_settings()


class GenerationResponse(BaseModel):
    status: str
    output_url: Optional[str] = None
    message: Optional[str] = None
    prompt_id: Optional[str] = None
    copy: Optional[str] = None
    palette: Optional[dict] = None


@router.post("/generate", response_model=GenerationResponse)
async def generate(
    generation_type: str = Form(...),
    prompt: str = Form(...),
    workspace_id: Optional[str] = Form(None),
    files: list[UploadFile] = File(default=[]),
):
    logger.info(f"Generation: type={generation_type}, workspace={workspace_id}")

    if generation_type == "image":
        return await _handle_image(prompt, workspace_id, files)
    elif generation_type == "video":
        return await _handle_video(prompt, workspace_id, files)
    elif generation_type == "copy":
        return await _handle_copy(prompt, workspace_id, files)
    elif generation_type == "palette":
        return await _handle_palette(prompt, workspace_id, files)
    elif generation_type == "vectorize":
        return await _handle_vectorize(prompt, workspace_id, files)
    raise HTTPException(status_code=400, detail=f"Unknown type: {generation_type}")


async def _send_to_comfyui(prompt_text: str, workflow: dict) -> JSONResponse:
    if not settings.COMFYUI_URL:
        raise HTTPException(status_code=503, detail="ComfyUI not configured.")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{settings.COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=600)
            if resp.status_code == 200:
                data = resp.json()
                return JSONResponse(content={"status": "pending", "message": "Generation queued in ComfyUI.", "prompt_id": data.get("prompt_id")})
            raise HTTPException(status_code=502, detail=f"ComfyUI error: {resp.text}")
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"ComfyUI failed: {str(e)}", "prompt_id": None})


async def _handle_image(prompt: str, workspace_id: Optional[str], files: list[UploadFile]) -> JSONResponse:
    workflow = {
        "3": {"inputs": {"seed": int(uuid.uuid4().hex[:8], 16) % (2**32), "steps": 20, "cfg": 8, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["6", 0], "positive": ["8", 0], "negative": ["9", 0], "vae": ["10", 0]}, "class_type": "KSampler"},
        "6": {"inputs": {"ckpt_name": "flux1-dev.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "8": {"inputs": {"text": prompt, "clip": ["6", 1]}, "class_type": "CLIPTextEncode"},
        "9": {"inputs": {"text": "blurry, ugly, deformed, noisy", "clip": ["6", 1]}, "class_type": "CLIPTextEncode"},
        "10": {"inputs": {"vae_name": "ae.safetensors"}, "class_type": "VAELoader"},
        "11": {"inputs": {"samples": ["3", 0], "vae": ["10", 0]}, "class_type": "VAEDecode"},
        "12": {"inputs": {"images": ["11", 0]}, "class_type": "SaveImage"},
    }
    return await _send_to_comfyui(prompt, workflow)


async def _handle_video(prompt: str, workspace_id: Optional[str], files: list[UploadFile]) -> JSONResponse:
    workflow = {
        "3": {"inputs": {"seed": int(uuid.uuid4().hex[:8], 16) % (2**32), "steps": 20, "cfg": 6, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["6", 0], "positive": ["8", 0], "negative": ["9", 0], "vae": ["10", 0]}, "class_type": "KSampler"},
        "6": {"inputs": {"ckpt_name": "wan2.2_ti2v_5B_fp16.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "8": {"inputs": {"text": prompt, "clip": ["6", 1]}, "class_type": "CLIPTextEncode"},
        "9": {"inputs": {"text": "blurry, low quality", "clip": ["6", 1]}, "class_type": "CLIPTextEncode"},
        "10": {"inputs": {"vae_name": "wan2.2_vae.safetensors"}, "class_type": "VAELoader"},
        "11": {"inputs": {"samples": ["3", 0], "vae": ["10", 0]}, "class_type": "VAEDecode"},
        "12": {"inputs": {"images": ["11", 0]}, "class_type": "SaveImage"},
    }
    return await _send_to_comfyui(prompt, workflow)


async def _handle_copy(prompt: str, workspace_id: Optional[str], files: list[UploadFile]) -> JSONResponse:
    if not settings.GROQ_API_KEY:
        return JSONResponse(content={"status": "error", "message": "Groq API not configured."})
    anti_ai = "Write natural, human-like copy. Use varied sentence lengths. Avoid AI-typical phrases. Use contractions. Include specific details. Write like a real person."
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={"model": "llama3-70b-8192", "messages": [
                    {"role": "system", "content": "You are an anti-AI copywriting engine."},
                    {"role": "user", "content": f"{anti_ai}\n\nGenerate copy:\n{prompt}"},
                ], "temperature": 0.8, "max_tokens": 2000},
                timeout=60,
            )
            if resp.status_code == 200:
                copy = resp.json()["choices"][0]["message"]["content"]
                return JSONResponse(content={"status": "success", "message": "Copy generated.", "copy": copy})
            return JSONResponse(content={"status": "error", "message": f"Groq error: {resp.text}"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Copy generation failed: {str(e)}"})


async def _handle_palette(prompt: str, workspace_id: Optional[str], files: list[UploadFile]) -> JSONResponse:
    if not files:
        return JSONResponse(content={"status": "error", "message": "Upload an image."})
    image_data = await files[0].read()
    try:
        from PIL import Image
        import numpy as np
        from sklearn.cluster import KMeans
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        img_array = np.array(image)
        pixels = img_array.reshape(-1, 3)
        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        kmeans.fit(pixels)
        centers = kmeans.cluster_centers_
        labels = kmeans.labels_
        counts = np.bincount(labels)
        sorted_indices = np.argsort(-counts)
        def rgb_to_hex(rgb): return f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"
        palette = {"primary": rgb_to_hex(centers[sorted_indices[0]]), "secondary": rgb_to_hex(centers[sorted_indices[1]]), "accent": rgb_to_hex(centers[sorted_indices[2]]), "neutral": rgb_to_hex(centers[sorted_indices[3]])}
        return JSONResponse(content={"status": "success", "message": "Palette extracted.", "palette": palette})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Palette extraction failed: {str(e)}"})


async def _handle_vectorize(prompt: str, workspace_id: Optional[str], files: list[UploadFile]) -> JSONResponse:
    if not files:
        return JSONResponse(content={"status": "error", "message": "Upload an image."})
    image_data = await files[0].read()
    try:
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        try:
            import vtracer
            import numpy as np
            img_array = np.array(image.convert("RGB"))
            result = vtracer.tracing(img_array, max_colors=16, type="color", scale=1.0, simplify_tolerance=0.2, inner_simplify_tolerance=0.1, dot_order=4, corner_threshold=45.0)
            svg_b64 = __import__("base64").b64encode(result.svg().encode()).decode()
            return JSONResponse(content={"status": "success", "message": "Vectorized.", "svg_base64": svg_b64, "width": image.width, "height": image.height})
        except ImportError:
            w, h = image.size
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="#e2e8f0"/><text x="{w//2}" y="{h//2}" text-anchor="middle" fill="#64748b" font-size="14">LUIN Vectorized</text></svg>'
            return JSONResponse(content={"status": "success", "message": "Fallback SVG (vtracer not installed).", "svg_string": svg})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Vectorization failed: {str(e)}"})
