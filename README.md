# Warrantrix Backend Deployment Guide

This repository contains the Warrantrix FastAPI backend. The notes below outline how to deploy the service on [Render](https://render.com/) using the included Dockerfile.

## Prerequisites

- Docker (optional for local testing)
- A Render account with access to Web Services and PostgreSQL
- A GitHub repository containing this project

## Local Docker Run

```bash
cd warrantrix_backend
docker build -t warrantrix-backend .
docker run --env-file .env -p 8000:8000 warrantrix-backend
```

The API will be available at http://localhost:8000. The health check endpoint lives at `GET /health` and the application routes are served under `/api/v1`.

## Deploying to Render

1. Push this repository to GitHub.
2. Create a **New Web Service** in Render.
   - Select the GitHub repository containing this project.
   - Choose **Docker** for the environment.
   - Render will automatically use the `Dockerfile` located in `warrantrix_backend/` and run the bundled `uvicorn` command.
   - Set the service name to match your desired subdomain (e.g. `warrantrix-backend`).
3. Provision a **Render PostgreSQL** instance.
   - Copy the connection string and add it as the `DATABASE_URL` environment variable for the web service.
4. Configure the following environment variables in Render (via the service dashboard):
   - `DATABASE_URL` – Render PostgreSQL connection string.
   - `OPENAI_API_KEY` – Optional, required for OpenAI features.
   - `JWT_SECRET_KEY` – Secret used to sign JWTs.
   - `JWT_ALGORITHM` – Defaults to `HS256` if not provided.
   - `ENV` – Set to `prod` in production.
   - `QDRANT_URL` and `QDRANT_API_KEY` – If using an external Qdrant instance.
   - `CORS_ORIGINS` – Comma-separated list of allowed origins (e.g. `http://localhost:5173,https://your-frontend.vercel.app`).
5. Trigger the initial deploy.
6. Once the deploy succeeds, verify the service:
   - `GET https://<service-name>.onrender.com/health` should return `{"status": "ok"}`.
   - API routes are available at `https://<service-name>.onrender.com/api/v1/...`.

The backend is now ready for your Vercel frontend or other clients. Update the `CORS_ORIGINS` environment variable whenever you need to allow additional origins.
