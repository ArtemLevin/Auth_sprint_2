FROM python:3.12-slim as builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /root/.cache/pip /root/.cache/pip
COPY --from=builder /usr/local /usr/local

COPY . .

RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app

USER appuser
WORKDIR /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]