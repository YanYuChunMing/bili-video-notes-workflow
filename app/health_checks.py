import os
import subprocess
from dataclasses import dataclass


@dataclass
class HealthCheckResult:
    name: str
    ok: bool
    status: str
    detail: str
    check_type: str
    version: str = ""
    error: str = ""


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _run_version_command(name: str, command: list[str]) -> HealthCheckResult:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except FileNotFoundError:
        return HealthCheckResult(
            name=name,
            ok=False,
            status="未检测到",
            detail=f"没有找到 {command[0]} 可执行文件。",
            check_type="command",
            error="command not found",
        )
    except Exception as exc:
        return HealthCheckResult(
            name=name,
            ok=False,
            status="检测失败",
            detail=str(exc),
            check_type="command",
            error=str(exc),
        )

    output = (result.stdout or "") + "\n" + (result.stderr or "")
    version = _first_non_empty_line(output)
    if result.returncode == 0:
        return HealthCheckResult(
            name=name,
            ok=True,
            status="可用",
            detail=version or f"{command[0]} 命令返回成功。",
            check_type="command",
            version=version,
        )

    return HealthCheckResult(
        name=name,
        ok=False,
        status="不可用",
        detail=version or f"{command[0]} 命令返回非 0 状态码。",
        check_type="command",
        version=version,
        error=output.strip(),
    )


def check_ffmpeg() -> HealthCheckResult:
    return _run_version_command("ffmpeg", ["ffmpeg", "-version"])


def check_ytdlp() -> HealthCheckResult:
    return _run_version_command("yt-dlp", ["yt-dlp", "--version"])


def check_deepseek_config(config: dict) -> HealthCheckResult:
    api_key = config.get("deepseek", {}).get("api_key", "")
    placeholders = ("请替换", "api密钥填这里", "your_key", "your-api-key")
    if not api_key:
        return HealthCheckResult(
            name="DeepSeek",
            ok=False,
            status="未配置",
            detail="仅做本地配置检测：没有读取到 DeepSeek API Key。",
            check_type="config_only",
        )

    if any(token in api_key.lower() for token in placeholders):
        return HealthCheckResult(
            name="DeepSeek",
            ok=False,
            status="疑似占位符",
            detail="仅做本地配置检测：API Key 看起来仍是占位符。",
            check_type="config_only",
        )

    source = ".env" if os.getenv("DEEPSEEK_API_KEY") else "config"
    return HealthCheckResult(
        name="DeepSeek",
        ok=True,
        status="已配置",
        detail=f"仅做本地配置检测：已从 {source} 读取 API Key，未联网验证可用性。",
        check_type="config_only",
    )


def run_health_checks(config: dict) -> list[HealthCheckResult]:
    return [
        check_ffmpeg(),
        check_ytdlp(),
        check_deepseek_config(config),
    ]
