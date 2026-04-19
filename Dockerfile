FROM python:3.12-slim

WORKDIR /bot

# 1. dependency layer (cache-friendly)
COPY requirements.txt .

RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# 2. app code (separate layer = cache ishlaydi)
COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "run.py"]
