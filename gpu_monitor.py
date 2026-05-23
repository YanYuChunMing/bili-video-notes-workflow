import subprocess
import sys
import os
import time
import threading
import signal
import json
import re
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(PROJECT_ROOT, ".trae", "specs", "gpu-health-check")
os.makedirs(REPORT_DIR, exist_ok=True)

FALLBACK_KEYWORDS = [
    "[CPU 回退]",
    "faster-whisper 在 device=",
    "openai-whisper (CPU 模式)",
    "回退到 CPU 解码",
]

GPU_SUCCESS_KEYWORDS = [
    "faster-whisper (CTranslate2)",
    "device=cuda",
    "device='cuda'",
]

GPU_LOG_FILE = os.path.join(PROJECT_ROOT, "gpu_monitor.log")
GPU_METRICS_FILE = os.path.join(REPORT_DIR, "gpu_metrics.jsonl")

stop_monitoring = threading.Event()
fallback_detected = threading.Event()
process_completed = threading.Event()

gpu_metrics = []
process_pid = None


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(GPU_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def monitor_nvidia_smi(interval: float = 2.0):
    global gpu_metrics
    while not stop_monitoring.is_set():
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=timestamp,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = [p.strip() for p in result.stdout.strip().split(",")]
                if len(parts) >= 6:
                    metric = {
                        "time": datetime.now().isoformat(),
                        "gpu_util_pct": parts[1],
                        "mem_used_mib": parts[2],
                        "mem_total_mib": parts[3],
                        "temp_c": parts[4],
                        "power_w": parts[5],
                    }
                    gpu_metrics.append(metric)
                    with open(GPU_METRICS_FILE, "a", encoding="utf-8") as f:
                        f.write(json.dumps(metric, ensure_ascii=False) + "\n")
        except Exception:
            pass
        time.sleep(interval)


def watch_output(pipe, prefix: str):
    global process_pid
    for line in iter(pipe.readline, ""):
        if stop_monitoring.is_set():
            break
        line = line.rstrip("\n\r")
        print(f"  [{prefix}] {line}", flush=True)

        for kw in FALLBACK_KEYWORDS:
            if kw in line:
                log(f"!!! GPU→CPU 回退检测到 !!! 关键词: '{kw}'")
                log(f"!!! 行内容: {line}")
                fallback_detected.set()
                break

        if fallback_detected.is_set():
            break

    pipe.close()


def collect_diagnostics() -> dict:
    diag = {
        "time": datetime.now().isoformat(),
        "event": "GPU_FALLBACK_DETECTED",
    }

    commands = {
        "nvidia_smi": "nvidia-smi",
        "nvidia_smi_detail": "nvidia-smi -q",
        "python_version": f'"{sys.executable}" --version',
        "pip_faster_whisper": f'"{sys.executable}" -m pip show faster-whisper ctranslate2',
        "pip_openai_whisper": f'"{sys.executable}" -m pip show openai-whisper',
        "env_cuda": "set | findstr /i cuda",
        "env_nvidia": "set | findstr /i nvidia",
    }

    for name, cmd in commands.items():
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=PROJECT_ROOT,
            )
            diag[name] = {
                "returncode": result.returncode,
                "stdout": result.stdout.strip()[:5000],
                "stderr": result.stderr.strip()[:2000],
            }
        except Exception as e:
            diag[name] = {"error": str(e)}

    diag["gpu_metrics_count"] = len(gpu_metrics)
    if gpu_metrics:
        diag["last_gpu_metric"] = gpu_metrics[-1]
        diag["first_gpu_metric"] = gpu_metrics[0]

    return diag


def save_diagnostics(diag: dict):
    path = os.path.join(REPORT_DIR, "fallback_diagnostics.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(diag, f, ensure_ascii=False, indent=2)
    log(f"诊断信息已保存到: {path}")
    return path


def analyze_fallback(diag: dict) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append("GPU→CPU 回退原因分析")
    lines.append("=" * 70)

    nvidia = diag.get("nvidia_smi_detail", {}).get("stdout", "")

    if "CUDA Version" in nvidia:
        cuda_ver_match = re.search(r"CUDA Version\s*:\s*(\S+)", nvidia)
        if cuda_ver_match:
            lines.append(f"  CUDA 驱动版本: {cuda_ver_match.group(1)}")

    mem_match = re.search(r"Used\s*:\s*(\d+)\s*MiB", nvidia)
    total_match = re.search(r"Total\s*:\s*(\d+)\s*MiB", nvidia)
    if mem_match and total_match:
        used = int(mem_match.group(1))
        total = int(total_match.group(1))
        lines.append(f"  显存使用: {used} MiB / {total} MiB ({used*100//total}%)")

    driver_match = re.search(r"Driver Version\s*:\s*(\S+)", nvidia)
    if driver_match:
        lines.append(f"  GPU 驱动版本: {driver_match.group(1)}")

    lines.append("")
    lines.append("  可能原因分析:")

    if mem_match and total_match:
        used = int(mem_match.group(1))
        if used / int(total_match.group(1)) > 0.95:
            lines.append("    ⚠ 显存不足（使用率 > 95%），模型加载或推理时 OOM")
        elif used / int(total_match.group(1)) > 0.85:
            lines.append("    ⚠ 显存紧张（使用率 > 85%），可能存在碎片化问题")

    lines.append("    - ctranslate2 CUDA 后端兼容性问题")
    lines.append("    - faster-whisper 模型与 CUDA 计算类型不兼容")
    lines.append("    - NVIDIA DLL 路径未正确配置")
    lines.append("    - GPU 驱动版本与 ctranslate2 内置库不匹配")
    lines.append("")
    lines.append("  建议操作:")
    lines.append("    1. 检查 config.toml 中 [whisper] device 是否为 'cuda'")
    lines.append("    2. 检查 [whisper] compute_type 是否为 'auto' 或 'float16'")
    lines.append("    3. 尝试 compute_type='int8_float16' 减少显存占用")
    lines.append("    4. 确认 nvidia\\cublas\\bin 和 nvidia\\cuda_runtime\\bin 目录存在")
    lines.append("    5. 尝试 model='small' 减少模型大小")
    lines.append("=" * 70)

    return "\n".join(lines)


def run():
    global process_pid

    log("=" * 60)
    log("GPU 监控视频处理流程启动")
    log(f"时间: {datetime.now().isoformat()}")
    log("=" * 60)

    gpu_available = subprocess.run(
        "nvidia-smi", shell=True, capture_output=True, timeout=10
    )
    if gpu_available.returncode != 0:
        log("错误: nvidia-smi 不可用，无法监控 GPU")
        return

    log("nvidia-smi 可用，GPU 监控已就绪")

    log("启动 main.py 处理 links_with_images.txt (mode=with_images)...")

    cmd = [
        sys.executable,
        "main.py",
        "--input", "links_with_images.txt",
        "--mode", "with_images",
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    process_pid = proc.pid
    log(f"main.py 进程已启动, PID={process_pid}")

    gpu_thread = threading.Thread(target=monitor_nvidia_smi, args=(1.5,), daemon=True)
    gpu_thread.start()

    stdout_thread = threading.Thread(target=watch_output, args=(proc.stdout, "OUT"), daemon=True)
    stderr_thread = threading.Thread(target=watch_output, args=(proc.stderr, "ERR"), daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    while True:
        if fallback_detected.is_set():
            log("!!! 检测到 GPU→CPU 回退，立即暂停进程 !!!")

            proc.terminate()
            time.sleep(2)
            if proc.poll() is None:
                proc.kill()
                time.sleep(1)

            stop_monitoring.set()
            process_completed.set()

            log("进程已终止，开始收集诊断信息...")
            diagnostics = collect_diagnostics()
            save_diagnostics(diagnostics)
            analysis = analyze_fallback(diagnostics)
            log(analysis)

            with open(os.path.join(REPORT_DIR, "fallback_analysis.txt"), "w", encoding="utf-8") as f:
                f.write(analysis)
            log(f"分析报告已保存到: {os.path.join(REPORT_DIR, 'fallback_analysis.txt')}")

            return False

        if proc.poll() is not None:
            exit_code = proc.returncode
            log(f"main.py 进程已结束, exit_code={exit_code}")
            stop_monitoring.set()
            process_completed.set()
            gpu_thread.join(timeout=5)
            return exit_code == 0

        time.sleep(0.3)


def main():
    success = run()

    print("\n" + "=" * 60)
    print("执行结果摘要")
    print("=" * 60)

    if fallback_detected.is_set():
        print("❌ GPU→CPU 回退事件已检测到并暂停!")
        print(f"   诊断报告: {os.path.join(REPORT_DIR, 'fallback_diagnostics.json')}")
        print(f"   分析报告: {os.path.join(REPORT_DIR, 'fallback_analysis.txt')}")
        print(f"   GPU 指标: {GPU_METRICS_FILE}")
        print(f"   监控日志: {GPU_LOG_FILE}")
    elif success:
        print("✅ 视频处理完成（GPU 加速稳定运行）")
    else:
        print("⚠ 进程异常退出（非 GPU 原因）")

    print(f"   监控日志: {GPU_LOG_FILE}")
    print(f"   GPU 指标: {GPU_METRICS_FILE}")
    print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
