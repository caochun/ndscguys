FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 数据目录由 Fly.io Volume 挂载，这里只确保目录存在（首次部署时用）
RUN mkdir -p /app/data

EXPOSE 8080

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "main:app"]
