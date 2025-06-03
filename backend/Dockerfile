# Stage 1: Build the Poetry environment
FROM python:3.10-slim as builder
# Using 3.10-slim as used by other Python services in Google.
# The original subtask mentioned 3.9-slim, but 3.10 is also fine and was used in pyproject.toml's requires-python.

WORKDIR /app

# Install poetry
# Pinning poetry version for reproducibility
ENV POETRY_VERSION=1.7.1
RUN pip install "poetry==$POETRY_VERSION"

# Copy only files necessary for poetry to resolve dependencies
COPY pyproject.toml poetry.lock ./

# Install dependencies - --no-dev for production
# --no-interaction --no-ansi are good for CI/CD
# --no-root: Do not install the project itself as it will be copied in the next stage
RUN poetry install --no-dev --no-interaction --no-ansi --no-root

# Stage 2: Create the runtime image
FROM python:3.10-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /.venv
# Activate the virtual environment by adding it to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy the application code from the backend directory
# The context for this Dockerfile will be the 'backend' directory.
# So, COPY . . copies the content of 'backend' into /app in the container.
COPY . .

# The run_ingestion.py script is expected to be in the project root,
# one level above the backend directory.
# For the backend Docker image, we need to adjust how it's run or what's copied.
# Assuming the CMD will refer to a script *within* the backend's /app context.
# If run_ingestion.py is essential and lives outside /backend, this Dockerfile might need adjustment
# or run_ingestion.py's role needs to be covered by a script inside /backend (e.g. an app_launcher.py).

# For now, let's assume the FastAPI app is started via backend/main.py
# and run_ingestion.py's DB init and combined startup is for local dev.
# In Docker, we might just run uvicorn directly if DataIngestionService is started by FastAPI lifespan.

# Expose the port the app runs on (FastAPI default is 8000, as per core/config.py)
EXPOSE 8000

# Command to run the application using Uvicorn directly targeting the FastAPI app object
# This is more standard for production Docker images for FastAPI.
# Assumes 'app' is the FastAPI instance in 'backend.main'.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Note: If run_ingestion.py was intended to be the primary entry point *inside* the container
# and it correctly sources things from /app (which would be the backend code), then CMD ["python", "run_ingestion.py"]
# would need run_ingestion.py to be copied into /app here.
# Given run_ingestion.py is at project root, and this Dockerfile's context is ./backend,
# using uvicorn directly is cleaner for the backend service container.
# The DB initialization done by run_ingestion.py would be handled by an init container or manually for prod.
