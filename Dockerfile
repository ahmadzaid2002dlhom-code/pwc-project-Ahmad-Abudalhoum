FROM node:22-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json .
RUN npm install

COPY frontend .
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY --from=frontend-builder /frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
