# syntax=docker/dockerfile:1

# ---- base: dependencias + código, compartido por dev y producción ----
FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PYTHONUNBUFFERED=1

# ---- dev: servidor local con hot reload (docker-compose monta el código) ----
FROM base AS dev

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---- lambda: misma imagen base + Lambda Web Adapter como extensión ----
# El adapter traduce eventos de Lambda (Function URL) a peticiones HTTP
# normales contra uvicorn en localhost:8080. No requiere ningún cambio
# de código (ni Mangum, ni handlers específicos de Lambda).
FROM base AS lambda

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
