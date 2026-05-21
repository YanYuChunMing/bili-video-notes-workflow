import subprocess, json, os, sys, ast

PROJECT_ROOT = r"d:\AAA_MY\AAAMyGit\bili_video"

print("=" * 60)
print("1. pyright 全项目静态类型检查")
print("=" * 60)

result = subprocess.run(
    ["pyright", PROJECT_ROOT, "--outputjson"],
    capture_output=True, text=True, timeout=60,
)
try:
    data = json.loads(result.stdout)
    diags = data.get("generalDiagnostics", [])
    print(f"诊断总数: {len(diags)}")
    errors = [d for d in diags if d.get("severity") == "error"]
    warns = [d for d in diags if d.get("severity") == "warning"]
    print(f"  errors: {len(errors)}, warnings: {len(warns)}")
    print()
    for d in diags:
        fname = d["file"].split("\\")[-1]
        line = d["range"]["start"]["line"] + 1
        sev = d["severity"]
        msg = d["message"]
        rule = d.get("rule", "")
        print(f"  {fname}:L{line} [{sev}] {msg}  ({rule})")
except Exception as e:
    print(f"pyright 解析失败: {e}")
    print("stdout:", result.stdout[:1000])

print()
print("=" * 60)
print("2. Python AST 编译检查")
print("=" * 60)

py_files = []
for root, dirs, files in os.walk(PROJECT_ROOT):
    dirs[:] = [d for d in dirs if not d.startswith(".")]
    for f in files:
        if f.endswith(".py"):
            py_files.append(os.path.join(root, f))

all_ok = True
for fpath in sorted(py_files):
    rel = os.path.relpath(fpath, PROJECT_ROOT)
    try:
        with open(fpath, "r", encoding="utf-8") as fh:
            source = fh.read()
        ast.parse(source, filename=rel)
        print(f"  ✅ {rel}")
    except SyntaxError as e:
        print(f"  ❌ {rel}  - SyntaxError: {e}")
        all_ok = False
    except Exception as e:
        print(f"  ⚠️ {rel}  - {type(e).__name__}: {e}")

if all_ok:
    print(f"\n  全部 {len(py_files)} 个文件 AST 编译通过")
