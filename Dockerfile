FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir yt-dlp -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

COPY . .

RUN mkdir -p outputs downloads logs

VOLUME ["/app/outputs", "/app/downloads", "/app/logs"]

ENTRYPOINT ["python", "main.py"]
CMD ["--task", "basic_test"]
