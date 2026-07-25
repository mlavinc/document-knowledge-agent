# syntax=docker/dockerfile:1

# ---- deps: instala dependencias (incluye devDependencies para el build) ----
FROM node:20-slim AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# ---- build: compila TypeScript -> dist/ ----
FROM deps AS build

COPY tsconfig.json ./
COPY src ./src
RUN npm run build

# ---- dev: servidor local con hot reload (docker-compose monta el código) ----
FROM deps AS dev

COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ---- prod-deps: solo dependencias de producción, para una imagen liviana ----
FROM node:20-slim AS prod-deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# ---- lambda: misma app compilada + Lambda Web Adapter como extensión ----
# El adapter traduce eventos de Lambda (integración con API Gateway HTTP
# API) a peticiones HTTP normales contra Express en localhost:8080. No
# requiere ningún cambio de código (ni serverless-http, ni handlers
# específicos de Lambda).
FROM node:20-slim AS lambda

WORKDIR /app

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./

ENV PORT=8080
EXPOSE 8080

CMD ["node", "dist/index.js"]
