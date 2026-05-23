import os
import glob
import subprocess
import webbrowser
import platform
from datetime import datetime


class FileManager:
    @staticmethod
    def get_output_dirs(output_base: str) -> list[dict]:
        if not os.path.isdir(output_base):
            return []
        dirs = []
        for entry in sorted(
            os.listdir(output_base),
            key=lambda e: os.path.getmtime(os.path.join(output_base, e)),
            reverse=True,
        ):
            full = os.path.join(output_base, entry)
            if not os.path.isdir(full):
                continue
            stat = os.stat(full)
            subdirs = [d for d in os.listdir(full) if os.path.isdir(os.path.join(full, d))]
            results_dir = os.path.join(full, "results")
            files = []
            if os.path.isdir(results_dir):
                files = sorted(os.listdir(results_dir))
            dirs.append({
                "name": entry,
                "path": full,
                "results_path": results_dir,
                "files": files,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "has_screenshots": any(
                    d.startswith("segment_") for d in subdirs
                ),
            })
        return dirs

    @staticmethod
    def get_output_files(output_dir: str) -> dict[str, list[str]]:
        result = {"txt": [], "md": [], "html": [], "json": [], "other": []}
        results_dir = os.path.join(output_dir, "results")
        if not os.path.isdir(results_dir):
            return result
        for f in sorted(os.listdir(results_dir)):
            full = os.path.join(results_dir, f)
            if not os.path.isfile(full):
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext == ".txt":
                result["txt"].append(f)
            elif ext == ".md":
                result["md"].append(f)
            elif ext == ".html":
                result["html"].append(f)
            elif ext == ".json":
                result["json"].append(f)
            else:
                result["other"].append(f)
        for f in sorted(os.listdir(output_dir)):
            full = os.path.join(output_dir, f)
            if os.path.isfile(full):
                ext = os.path.splitext(f)[1].lower()
                if ext == ".txt":
                    result["txt"].append(f"../{f}")
                elif ext == ".md":
                    result["md"].append(f"../{f}")
                elif ext == ".json":
                    result["json"].append(f"../{f}")
                else:
                    result["other"].append(f"../{f}")
        return result

    @staticmethod
    def read_file(filepath: str) -> str:
        if not os.path.isfile(filepath):
            return ""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(filepath, "r", encoding="gbk") as f:
                    return f.read()
            except Exception:
                return f"[无法读取: 编码错误] {filepath}"
        except Exception as e:
            return f"[读取错误: {e}]"

    @staticmethod
    def open_folder(path: str) -> bool:
        if not os.path.isdir(path):
            return False
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
            return True
        except Exception:
            return False

    @staticmethod
    def open_in_browser(filepath: str) -> bool:
        if not os.path.isfile(filepath):
            return False
        try:
            abs_path = os.path.abspath(filepath)
            webbrowser.open(f"file://{abs_path}")
            return True
        except Exception:
            return False

    @staticmethod
    def open_with_default_app(filepath: str) -> bool:
        if not os.path.isfile(filepath):
            return False
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(filepath)
            elif system == "Darwin":
                subprocess.Popen(["open", filepath])
            else:
                subprocess.Popen(["xdg-open", filepath])
            return True
        except Exception:
            return False

    @staticmethod
    def find_screenshot_files(output_dir: str) -> list[dict]:
        screenshots = []
        patterns = [
            os.path.join(output_dir, "segment_*", "images", "*"),
            os.path.join(output_dir, "segment_*", "*"),
            os.path.join(output_dir, "images", "*"),
        ]
        seen = set()
        for pattern in patterns:
            for full in sorted(glob.glob(pattern)):
                if not os.path.isfile(full):
                    continue
                if not full.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    continue
                if full in seen:
                    continue
                seen.add(full)
                rel = os.path.relpath(full, output_dir)
                parts = rel.split(os.sep)
                screenshots.append({
                    "segment": parts[0] if parts else "",
                    "filename": os.path.basename(full),
                    "path": full,
                    "relative": rel,
                })
        return screenshots
