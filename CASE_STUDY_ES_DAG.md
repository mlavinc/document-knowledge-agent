# Document Knowledge Agent

Document Knowledge Agent es un sistema de Retrieval-Augmented Generation (RAG) para bases de conocimiento a partir de PDFs. El usuario sube un documento, hace preguntas en lenguaje natural y recibe respuestas ancladas a fragmentos recuperados, con metadatos de fuente que indican qué documentos respaldaron la respuesta.

El mismo backend alimenta una segunda superficie: un asistente de portafolio tipo “pregúntame lo que quieras”, que consulta un corpus aislado (perfil, experiencia, proyectos) en lugar de los papers subidos por el usuario.

Demo en vivo: https://document-knowledge-agent-tau.vercel.app/

`[Captura: UI de demo con carga de PDF y preguntas con fuentes]`

## Motivación / Problema

Construí este proyecto para entender cómo funciona un pipeline RAG completo en la práctica, no solo como experimento en un notebook. El punto de partida fue un agente orientado a ArXiv: buscar papers, ingerir PDFs, embeberlos en local con Ollama y Chroma, y responder preguntas sobre ese corpus. La estructura por sprints del repositorio todavía refleja ese camino.

A medida que el sistema maduró, el problema interesante cambió. Quería un producto de preguntas sobre documentos que pudiera correr totalmente offline en desarrollo y desplegarse en AWS sin reescribir la aplicación por entorno. La búsqueda por palabras clave encaja mal con PDFs técnicos largos; la recuperación semántica más generación anclada es una mejor aproximación, pero solo si la arquitectura aguanta restricciones reales de nube (timeouts, secretos, cold starts, costo).

El asistente de portafolio llegó después, como prueba de productización: reutilizar la misma API de búsqueda sobre una base de conocimiento curada, mantener el corpus de demo aislado y exponer el resultado como un chat que un visitante puede probar.

## Arquitectura

El sistema se divide en tres capas de aplicación, más la infraestructura definida en Terraform.

```text
Navegador (React / Vite)
        │
        ▼
API Gateway (Express / TypeScript)
  valida entrada, maneja uploads, hace proxy a rag-core
  producción: IAM SigV4, ingest asíncrono vía Lambda Event
        │
        ▼
RAG Core (FastAPI / Python)
  parsear → fragmentar → embeber → guardar
  recuperar → generar
        │
        ├── Local:  Ollama + Chroma + filesystem
        └── Prod:   OpenAI + Aurora pgvector (Data API) + S3
```

`[Diagrama de arquitectura: stack Compose local vs ruta serverless en AWS]`

El gateway se mantiene deliberadamente delgado. Se ocupa de lo HTTP (CORS, Helmet, validación con Zod, upload multipart, códigos de respuesta). RAG Core concentra el pipeline: extracción con PyMuPDF, fragmentación de tamaño fijo (1000 caracteres, solape de 200), embeddings, búsqueda vectorial y generación con LLM mediante providers respaldados por LangChain.

El enrutamiento de corpus usa el header `X-RAG-Collection` (`default` o `portfolio`). FastAPI guarda esa elección en un contexto por request y resuelve colecciones Chroma o tablas Aurora distintas (`document_chunks_openai` frente a `document_chunks_portfolio` en producción).

Ambas Lambdas corren imágenes de contenedor con AWS Lambda Web Adapter, de modo que las mismas apps FastAPI y Express escuchan HTTP sin Mangum ni handlers a medida. CloudFront sirve el SPA desde S3 y puede reenviar `/api/*` al HTTP API.

## Decisiones de ingeniería

**Gateway Node delgado y núcleo RAG en Python.**  
El Sprint 1 fijó este límite desde el inicio. Python es el lugar natural para parseo de PDF, embeddings y clientes vectoriales. Express encaja mejor como borde público tipado, con middleware y manejo de uploads. El costo es un hop de red extra y dos unidades desplegables; a cambio, cada capa escala y evoluciona por su cuenta.

**Facades de provider en lugar de ramas por entorno.**  
`LLM_PROVIDER`, `EMBEDDING_PROVIDER`, `VECTOR_DB_PROVIDER` y `STORAGE_PROVIDER` eligen implementaciones en runtime. En local, el default es Ollama (`qwen2.5:3b`, `nomic-embed-text`), Chroma y filesystem. En producción, Terraform configura OpenAI (`gpt-4.1-mini`, `text-embedding-3-small`), Aurora pgvector y S3. Cambiar de provider es configuración, no reescribir la orquestación RAG.

**OpenAI en producción tras Bedrock.**  
Una ruta de producción anterior usaba Bedrock. El historial de commits registra mitigaciones de throttling (backoff, concurrencia acotada) y una migración posterior a OpenAI. El código actual y `DEPLOY.md` no dependen de Bedrock; la API key vive en SSM SecureString y se carga en runtime solo por nombre del parámetro.

**Ingest asíncrono solo donde el timeout lo obliga.**  
En local, el ingest es síncrono: Compose no tiene el límite de ~29 segundos de API Gateway y Ollama está en la misma red. En producción, el gateway responde `202`, invoca rag-core con `InvocationType=Event` usando un payload con forma de Function URL (para que Lambda Web Adapter siga funcionando), y el frontend hace polling de estado. La búsqueda permanece síncrona. El timeout de la Lambda del gateway es 30 segundos; rag-core puede llegar a 300.

**IAM en la Function URL de rag-core.**  
rag-core no es un endpoint público. El gateway firma las llamadas salientes con SigV4 cuando `RAG_CORE_AUTH_MODE=iam`. Además de la política IAM del caller, hizo falta un permiso resource-based en la Lambda; sin eso, las invocaciones fallaban con 403.

**Aurora Serverless v2 + RDS Data API.**  
pgvector corre en Aurora con acceso HTTP por Data API para que las Lambdas no entren a la VPC (sin costo de NAT/ENI en un workload de portafolio). El bootstrap del esquema se ejecuta una vez en `terraform apply` con un script Python local, no en cada request. La capacidad mínima es 0; el cliente reintenta ante `DatabaseResumingException` cuando el cluster despierta.

**Corpus de portafolio aislado sobre la misma API.**  
En lugar de levantar un segundo backend, el frontend de portafolio solo llama a `POST /api/search` con `X-RAG-Collection: portfolio`. La expansión de query reescribe preguntas deícticas (“tú/tu”) solo para el embedding; la pregunta original sigue yendo al LLM. Así la recuperación sirve para un chat en primera persona sin alterar el camino de la demo.

## Desafíos

**Timeout duro de API Gateway frente a ingest largo de PDF.**  
Parsear, fragmentar, embeber y guardar puede superar ~29 segundos. La solución no fue “hacer el ingest más rápido”, sino desacoplar el acuse de recibo del trabajo. Marcadores de estado en storage (`processing` → `completed`/`failed`) permiten al UI hacer polling con seguridad, incluido un fallback a `processing` si el marcador aún no existe.

**Fiabilidad en producción bajo restricciones de costo serverless.**  
Aurora con capacidad mínima 0 implica latencia de resume en clusters fríos. Las llamadas de embedding necesitaron políticas de reintento distintas para query e ingestión. Las imágenes de Lambda tuvieron que construirse con `docker buildx` usando `--provenance=false --sbom=false`, porque Lambda rechaza ciertos manifiestos OCI de BuildKit.

**Los espacios vectoriales local y producción no son intercambiables.**  
Los embeddings locales tienen 768 dimensiones (`nomic-embed-text`); producción usa 1536 (`text-embedding-3-small`). Las tablas y scripts de bootstrap toman `EMBEDDING_DIMENSIONS` de forma explícita para que el ancho del esquema coincida con el modelo activo.

**Evitar que dos superficies de producto se contaminen.**  
Las subidas de la demo y los documentos del portafolio comparten infraestructura, pero no índices. Nombres de tabla conscientes de la colección, prefijos en S3 y validación del header impiden que un paper responda a “cuéntame de tu práctica en Nestlé” (y al revés).

## Resultados

- Stack local de punta a punta con Docker Compose (Ollama, rag-core, api-gateway, frontend).
- Ruta de producción definida en Terraform: ECR, dos Lambdas en contenedor, HTTP API, CloudFront, S3, Aurora pgvector, parámetro SSM y una alerta de AWS Budgets de 5 USD/mes en bootstrap.
- UI de demo en Vercel apoyada en la API de AWS.
- API Gateway cubierto con Vitest + Supertest (health, validación/proxy de search, validación/proxy de documents, comportamiento `202` del ingest asíncrono).
- El asistente de portafolio reutiliza el mismo contrato de búsqueda sobre un corpus curado en `portfolio_documents/`.

No se afirman aquí benchmarks de latencia ni de calidad de recuperación; no quedaron establecidos como resultados medidos del proyecto.

`[Flujo de despliegue: terraform apply → push de imagen → update de Lambda → sync del frontend]`

## Qué aprendí

- Los timeouts de la nube condicionan el diseño de la API más que la elección del modelo. Búsqueda síncrona e ingest asíncrono son contratos distintos por una razón.
- Las abstracciones de provider solo valen si local y producción son honestos sobre sus diferencias (dimensiones, storage, modo de auth).
- Un RAG serverless no es solo “poner FastAPI en Lambda”: son secretos, comportamiento de resume, empaquetado de imágenes y quién puede hablar con qué endpoint.
- Una segunda superficie de producto (chat de portafolio) es una buena prueba de si límites como colecciones y prompts están realmente aislados.

## Mejoras futuras

- Autenticación de usuario final y espacios de documentos por usuario (la API pública hoy no tiene auth más allá de la validación en el borde y el IAM entre servicios).
- Un harness real de evaluación para calidad de retrieval y respuestas (hoy solo hay un script de regresión del portafolio).
- Conectar o eliminar `packages/rag-ui-shared`; ambos frontends son autónomos por ahora.
- Definir el destino de las rutas ArXiv que quedan en rag-core y no se exponen por el gateway público.
