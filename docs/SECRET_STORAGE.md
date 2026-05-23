# 本地 API Key 存储说明

本项目不再把 DeepSeek API Key 写入 `.env` 或 `config.toml`。Web 页面输入 API Key 后，会调用后端 `app.secret_store` 写入本地 SQLite 密钥库。

## 本机运行

- 默认数据库：`temp/local_secrets.sqlite3`
- Windows：优先使用 DPAPI 加密，只有当前 Windows 用户能解密。
- 页面不会显示 API Key 的任何片段。

## Docker 运行

Docker 使用持久化目录：

```yaml
./secrets:/app/secrets
```

数据库路径：

```text
/app/secrets/local_secrets.sqlite3
```

容器内没有 Windows DPAPI，因此需要设置口令：

```powershell
$env:BILI_SECRET_PASSPHRASE="your-local-passphrase"
docker compose --profile web up bili-video-web
```

没有 `BILI_SECRET_PASSPHRASE` 时，容器会拒绝保存 API Key，避免明文落盘。

## 安全边界

- 不要提交 `secrets/`、`*.sqlite3` 或旧 `.env`。
- 如果旧 `.env` 曾保存真实 Key，建议删除 `.env` 中的 Key，并在 DeepSeek 平台轮换密钥。
