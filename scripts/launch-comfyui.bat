@echo off
echo Starting LUIN ComfyUI (Flux.1 Dev + Wan2.2)...
echo Make sure models are installed in your ComfyUI custom_nodes and models folders.
echo.
cd /d C:\AI\ComfyUI
python main.py --enable-cors-header --port 8188
pause
