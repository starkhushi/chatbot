# Dockerfile - FOR DOCKER/PRODUCTION DEPLOYMENT
# For local testing, you don't need this - just run: sh run.sh
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "run.sh"]