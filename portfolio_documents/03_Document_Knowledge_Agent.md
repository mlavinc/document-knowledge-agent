# 03 — Project: Document Knowledge Agent

## Overview

**Document Knowledge Agent** (also called **Document RAG Agent**, **Document RAG Knowledge Agent**, or **DAG**) is one of Martín Lavín's (Martin Lavin) main portfolio projects.

It is a cloud-native Retrieval-Augmented Generation (RAG) system that lets users upload documents and ask natural-language questions about their content. Documents are parsed, chunked, embedded, and stored for semantic search. Answers are grounded in retrieved passages and include sources.

Repository: github.com/mlavinc/document-knowledge-agent

## What problem it solves

Instead of manually searching long PDFs, users upload a document once and ask questions. The system retrieves the most relevant fragments and generates a grounded answer with source transparency.

## Architecture (high level)

User → Frontend → API Gateway → Backend / RAG Core → Document processing → Vector database + LLM

Key capabilities:
- PDF upload and ingestion
- Text extraction and cleaning
- Chunking for retrieval
- Semantic search with embeddings
- Grounded Q&A with sources
- Asynchronous document processing
- Cloud-ready local/cloud deployment patterns

## Technology stack

- Frontend: React, TypeScript
- API Gateway: Node.js / Express
- RAG backend: Python, FastAPI
- AI / retrieval: embeddings, vector search, foundation models
- Data: Aurora / PostgreSQL with pgvector (production path)
- Cloud: AWS Lambda, API Gateway, S3, CloudFront, Terraform
- Related concepts: microservices, semantic search, RAG pipeline

(Earlier portfolio descriptions also mention AWS Bedrock Titan + Claude Haiku as one provider option in the project evolution.)

## Natural-language Q&A

**Explain the Document Knowledge Agent / What is the Document Knowledge Agent?**
It is Martín's full-stack RAG system for intelligent document Q&A: upload PDFs, retrieve relevant chunks via embeddings/vector search, and answer with source-backed LLM responses on AWS.

**What projects has Martin built?** (this project is one of them)
Document Knowledge Agent is one of his flagship projects alongside Cloud Operations Lab, ECG AI Serverless, and Skill Tracker.

**What did you build? / Tell me about your RAG project.**
Martín built a production-oriented Document Knowledge Agent with FastAPI, vector search (pgvector), Lambda-based services, Terraform infrastructure, and a React frontend so users can chat with their documents.
