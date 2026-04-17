FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

ENV MP_API_HOST=0.0.0.0
ENV MP_API_PORT=8080
ENV MP_PALACE_PATH=/data/.mempalace

CMD ["python", "main.py"]
