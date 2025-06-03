# Deployment Guide

This document provides guidance on deploying the Crypto Dashboard application.

## 1. Overview
The recommended deployment method involves containerizing the frontend and backend applications using Docker and managing them with Docker Compose for local development or testing environments. For production, deploying these containers to a cloud platform or a dedicated server with proper orchestration is advised.

## 2. Prerequisites
*   Docker installed ([https://www.docker.com/get-started](https://www.docker.com/get-started)).
*   Docker Compose installed (usually included with Docker Desktop, or as a separate plugin).
*   Git (for cloning the repository).

## 3. Project Structure for Docker
The project contains:
*   `backend/Dockerfile`: Defines the image for the Python FastAPI backend.
*   `frontend/Dockerfile`: Defines the image for the React frontend, served by Nginx.
*   `frontend/nginx.conf`: Nginx configuration for serving the frontend and handling client-side routing.
*   `docker-compose.yml`: Located in the project root, orchestrates the multi-container application (backend, frontend, database).
*   `.env` (project root): Used by Docker Compose to supply environment variables to services (e.g., database credentials).

## 4. Local Deployment with Docker Compose

This is the simplest way to get the entire application stack running locally.

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Configure Environment Variables:**
    *   Create a `.env` file in the project root (same directory as `docker-compose.yml`). You can copy `env.example` if provided, or create it manually.
    *   Define at least the following for the database service:
        ```env
        POSTGRES_USER=user
        POSTGRES_PASSWORD=yoursecretpassword # IMPORTANT: Change this to a strong password
        POSTGRES_DB=crypto_dashboard
        ```
    *   The `DATABASE_URL` for the backend service is constructed automatically in `docker-compose.yml` using these values, pointing to the `db` service.
    *   You can also set `LOG_LEVEL` for the backend (e.g., `LOG_LEVEL=INFO`).

3.  **Build and Run with Docker Compose:**
    *   From the project root directory (where `docker-compose.yml` is located), run:
        ```bash
        docker-compose up --build -d
        ```
        *   `--build`: Forces Docker to build the images from the Dockerfiles (needed for the first run or after code changes).
        *   `-d`: Runs the containers in detached mode (in the background).
    *   To view logs: `docker-compose logs -f backend frontend db`
    *   To stop services: `docker-compose down`

4.  **Accessing the Application:**
    *   **Frontend:** `http://localhost:3000` (Nginx in the frontend container serves on port 80, which is mapped to 3000 on the host).
    *   **Backend API:** `http://localhost:8000` (FastAPI/Uvicorn in the backend container serves on port 8000, mapped to 8000 on the host).
    *   **API Docs (Swagger UI):** `http://localhost:8000/docs`

5.  **Database Initialization:**
    *   The backend application (specifically `run_ingestion.py` via FastAPI lifespan events) attempts to initialize the database schema (`init_db.py`) on startup.
    *   The `depends_on.db.condition: service_healthy` in `docker-compose.yml` ensures the backend waits for the database to be ready.

## 5. Building Images Manually (Optional)
If you want to build images individually without `docker-compose`:
*   **Backend:**
    ```bash
    cd backend
    docker build -t crypto-dashboard-backend:latest .
    ```
*   **Frontend:**
    ```bash
    cd frontend
    docker build -t crypto-dashboard-frontend:latest .
    ```

## 6. Production Deployment Considerations

Deploying to a production environment requires additional considerations beyond the scope of this local Docker Compose setup.

*   **Database:**
    *   Use a managed TimescaleDB/PostgreSQL service from a cloud provider (e.g., AWS RDS, Google Cloud SQL, Azure Database for PostgreSQL, Timescale Cloud).
    *   Ensure regular backups, monitoring, and appropriate resource allocation.
    *   Configure `DATABASE_URL` in the backend environment securely.
*   **Backend (FastAPI Application):**
    *   Build a production-ready Docker image (the provided `backend/Dockerfile` is a good start; ensure no development volumes are mounted).
    *   Push the image to a container registry (e.g., Docker Hub, AWS ECR, Google Artifact Registry, Azure Container Registry).
    *   Deploy to a container orchestration platform (e.g., Kubernetes, AWS ECS, Google Cloud Run, Azure App Service / Container Instances).
    *   Manage environment variables and secrets securely (e.g., using HashiCorp Vault, AWS Secrets Manager, Google Secret Manager, Azure Key Vault).
    *   Scale the number of backend instances based on load.
*   **Frontend (React/Nginx Application):**
    *   Build a production-ready Docker image (the provided `frontend/Dockerfile` is suitable).
    *   Push the image to a container registry.
    *   Deploy using a service optimized for static content delivery (e.g., AWS S3 + CloudFront, Google Cloud Storage + Cloud CDN, Netlify, Vercel) or host the Nginx container on a container platform.
    *   If serving frontend and backend from different domains, configure CORS appropriately on the backend. If using Nginx as a reverse proxy (as commented out in `frontend/nginx.conf`), ensure it's configured correctly to route API calls to the backend service.
*   **ML Models:**
    *   The current setup simulates model loading. For real models:
        *   Ensure model files (`.pkl` or other formats) are included in the backend Docker image or made available via a mounted volume or by downloading from a secure model registry/storage (e.g., AWS S3, MLflow Model Registry) at container startup.
        *   Update `MOMENTUM_SUSTAINABILITY_MODEL_PATH`, `BREAKOUT_VIABILITY_MODEL_PATH`, `ABSORPTION_OUTCOME_MODEL_PATH` in the backend configuration to point to the correct paths *within the container*.
*   **Networking:**
    *   Set up DNS records for your domain(s).
    *   Use a load balancer in front of your backend services.
    *   Implement SSL/TLS for HTTPS.
*   **Logging and Monitoring:**
    *   Aggregate logs from all services into a centralized logging system (e.g., ELK stack, Grafana Loki, Datadog, Splunk).
    *   Implement application performance monitoring (APM) and infrastructure monitoring.
*   **Security:**
    *   Regularly update dependencies and base Docker images.
    *   Secure API endpoints (e.g., authentication/authorization if needed beyond public data).
    *   Follow security best practices for web applications and cloud deployments.
```
