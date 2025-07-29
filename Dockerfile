FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --no-cache-dir pytest flake8

RUN mkdir -p /app/data /app/json

VOLUME ["/app/data"]

# Default command
CMD ["make", "run"]