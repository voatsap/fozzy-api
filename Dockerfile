# Use a lightweight Python image
FROM python:3.10-slim

# Ensures stdout/stderr is unbuffered so logs appear immediately in Docker logs
ENV PYTHONUNBUFFERED=1

# (Optional) Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Create a working directory for the app
WORKDIR /app

# Copy requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code including:
#  - api.py
#  - pyproject.toml
#  - fozzy_dataframe.bin (the pickle file)
COPY . .

# Expose the port FastAPI/Uvicorn will run on
EXPOSE 8000

# Use Uvicorn as the entrypoint. Adjust host/port as needed.
#CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "api:app", "--bind", "0.0.0.0:8000", "--workers", "4"]