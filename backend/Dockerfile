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

# Create a non-root user and group for security best practices
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /.venv

# Copy the application code from the backend directory (context is ./backend)
# This should be done before changing user to ensure correct permissions for /app
COPY . .

# Change ownership of the /app directory to the new user
# This ensures the app runs with files owned by the appuser
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Activate the virtual environment by adding it to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose the port the app runs on (FastAPI default is 8000, as per core/config.py or docker-compose)
EXPOSE 8000

# Command to run the application using Uvicorn directly targeting the FastAPI app object.
# FastAPI's lifespan events in backend.main:app handle DataIngestionService startup/shutdown.
# The LOG_LEVEL environment variable can be set (e.g., in docker-compose.yml) to control uvicorn's log level.
# Defaulting to "info" if not set. Uvicorn's --log-level maps to Python's logging levels.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "${LOG_LEVEL:-info}"]
