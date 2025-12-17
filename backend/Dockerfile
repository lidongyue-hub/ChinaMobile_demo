FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖（如需 mysqlclient 可在此添加 libmysqlclient-dev 等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

# 安装 uv 并用它安装依赖
RUN pip install --no-cache-dir uv
RUN uv pip install --system -e .

COPY src ./src

# 预创建上传目录
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

