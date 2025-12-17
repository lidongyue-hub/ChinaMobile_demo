# Backend - AI 对话与会话管理

本目录包含基于 FastAPI + MySQL + LLM 的后端服务代码，支持：
- 会话创建与历史保存（会话表 + 消息表）
- 文件上传（存储于 uploads/），结合用户消息交给 LLM 回复
- 会话名称自动生成（若未指定，则用首条用户消息由 LLM 生成简短标题）

## 环境准备（使用 uv 和 Python 3.12）

在项目根目录下（或切换到 `backend` 目录）执行：

```bash
cd backend
# 创建 Python 3.12 虚拟环境
uv venv -p 3.12 .venv

# 激活虚拟环境（不同 shell 略有差异）
source .venv/bin/activate

# 安装依赖
uv pip install -e .
```

> 如果不使用 `uv pip install -e .`，也可以直接：
>
> ```bash
> uv pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncmy pydantic python-multipart python-dotenv httpx
> ```

## 运行开发服务器

```bash
cd backend
uvicorn src.main:app --reload
```

API 文档地址（启动后）：

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 主要接口（会话与消息）
- `POST /conversations`：创建会话，发送首条消息（可选上传文件）；若未提供 name，会自动生成标题；返回助手首答。
- `GET /conversations`：会话列表。
- `GET /conversations/{id}`：会话详情（含消息列表）。
- `POST /conversations/{id}/messages`：在会话中继续对话（可选文件、可选指定模型）。
- `GET /conversations/{id}/messages`：分页拉取消息历史。
- `GET /health`：健康检查。

文件存储：上传文件保存到 `uploads/`（容器中为 `/app/uploads`），建议使用定期任务每 3 天清理一次过期文件。

## 代码格式化 / pre-commit

- 安装 pre-commit（可用 pipx/uv/pip）：

```bash
pip install pre-commit
# 或 pipx install pre-commit
# 或 uv tool install pre-commit
```

- 在 backend 目录安装 hook：

```bash
cd backend
pre-commit install
```

- 手动全量检查：

```bash
pre-commit run --all-files
```

Hook 组合：black + isort + ruff（自动修复开启）。

