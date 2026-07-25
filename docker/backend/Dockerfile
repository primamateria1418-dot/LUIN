FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Add backend/ to the Python path so sibling modules (config, routes, modules) are importable
ENV PYTHONPATH=/app/backend

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code (backend/ is inside the build context)
COPY backend/ ./backend/

# Expose the port
EXPOSE 8000

# Start Uvicorn against the FastAPI app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
