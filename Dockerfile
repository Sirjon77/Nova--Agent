
# Nova Agent Dockerfile
#
# This image builds and runs the Nova Agent backend. It bases off of a
# slim Python 3.10 image, installs all Python dependencies, copies
# the application code and exposes the FastAPI app via Uvicorn on
# port 8000. Adjustments can be made via environment variables at
# runtime (e.g. to set the log level or change the host/port).

FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Install Python dependencies. Using --no-cache-dir reduces image size.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Ensure Python output is not buffered
ENV PYTHONUNBUFFERED=1

# Expose the FastAPI port
EXPOSE 8000

# Use Uvicorn to serve the FastAPI application. Adjust the host and
# port here or via command-line when running the container. We
# specify the application as "nova.api.app:app" to point Uvicorn to
# the `app` object defined in nova/api/app.py.
CMD ["uvicorn", "nova.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
