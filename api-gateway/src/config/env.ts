import dotenv from "dotenv";

dotenv.config();

export const env = {
  PORT: Number(process.env.PORT) || 3000,
  RAG_CORE_URL: process.env.RAG_CORE_URL || "http://localhost:8000",
  CORS_ORIGIN: process.env.CORS_ORIGIN || "http://localhost:5173",
  AWS_REGION: process.env.AWS_REGION || "us-east-1",
  // "none" en desarrollo local; "iam" en producción, donde rag-core se
  // expone mediante una Lambda Function URL con autenticación IAM y las
  // peticiones deben firmarse con SigV4.
  RAG_CORE_AUTH_MODE: (process.env.RAG_CORE_AUTH_MODE || "none") as
    | "none"
    | "iam",
};
