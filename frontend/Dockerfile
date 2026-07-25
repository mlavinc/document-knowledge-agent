# syntax=docker/dockerfile:1

# ---- deps ----
FROM node:20-slim AS deps

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

# ---- dev: servidor Vite con hot reload (docker-compose monta el código) ----
FROM deps AS dev

COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ---- build: genera los estáticos que se suben a S3 en producción ----
# Esta etapa no corre como contenedor en AWS: el resultado (/app/dist) se
# sincroniza al bucket S3 servido por CloudFront (ver comandos de deploy).
# VITE_API_GATEWAY_URL se deja vacío en producción: CloudFront sirve el
# frontend y la API bajo el mismo dominio, por lo que las llamadas a
# /api/* son same-origin y no requieren una URL absoluta.
FROM deps AS build

ARG VITE_API_GATEWAY_URL=""
ENV VITE_API_GATEWAY_URL=${VITE_API_GATEWAY_URL}

COPY . .
RUN npm run build
