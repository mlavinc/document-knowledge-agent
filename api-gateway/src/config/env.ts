import dotenv from "dotenv";

dotenv.config();

export const env = {
  PORT: Number(process.env.PORT) || 3000,
  RAG_CORE_URL: process.env.RAG_CORE_URL || "http://localhost:8000",
  CORS_ORIGIN: process.env.CORS_ORIGIN || "http://localhost:5173",
  AWS_REGION: process.env.AWS_REGION || "sa-east-1",
  // "none" en desarrollo local; "iam" en producción, donde rag-core se
  // expone mediante una Lambda Function URL con autenticación IAM y las
  // peticiones deben firmarse con SigV4.
  RAG_CORE_AUTH_MODE: (process.env.RAG_CORE_AUTH_MODE || "none") as
    | "none"
    | "iam",
  // "sync" en desarrollo local: la petición espera la respuesta completa
  // de rag-core (Ollama es rápido y no hay límite de 30s de API Gateway).
  // "async" en producción: rag-core se invoca de forma nativa y asíncrona
  // (Lambda InvocationType=Event) para desacoplar la ingestión —que puede
  // tardar varios minutos por el pacing/retries de Bedrock— del timeout
  // fijo de ~29s de API Gateway HTTP API. El Gateway responde 202 de
  // inmediato y rag-core sigue procesando en su propia invocación Lambda.
  INGESTION_MODE: (process.env.INGESTION_MODE || "sync") as "sync" | "async",
  // Nombre (no ARN) de la función Lambda de rag-core, requerido para
  // invocarla directamente vía el SDK de Lambda en modo "async".
  RAG_CORE_FUNCTION_NAME: process.env.RAG_CORE_FUNCTION_NAME || "",
};
