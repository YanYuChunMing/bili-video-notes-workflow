import os
import logging

from openai import OpenAI

from . import utils

logger = logging.getLogger(__name__)

MINDMAP_HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>思维导图</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
    background: #f5f5f5;
    padding: 2rem;
  }
  .mindmap {
    max-width: 900px;
    margin: 0 auto;
    background: #fff;
    border-radius: 12px;
    padding: 2rem 3rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  }
  .mindmap h1 {
    font-size: 1.8rem;
    color: #1a1a2e;
    border-bottom: 3px solid #4a90d9;
    padding-bottom: 0.5rem;
    margin-bottom: 1.5rem;
  }
  .mindmap h2 {
    font-size: 1.3rem;
    color: #2c3e50;
    margin: 1.5rem 0 0.8rem;
    padding-left: 0.5rem;
    border-left: 4px solid #4a90d9;
  }
  .mindmap h3 {
    font-size: 1.1rem;
    color: #34495e;
    margin: 1rem 0 0.5rem 1.5rem;
  }
  .mindmap ul {
    list-style: disc;
    padding-left: 3rem;
    margin-bottom: 1rem;
  }
  .mindmap li {
    margin: 0.3rem 0;
    line-height: 1.7;
    color: #555;
  }
</style>
</head>
<body>
<div class="mindmap">
{mindmap_content}
</div>
</body>
</html>'''


def _create_client(config: dict) -> OpenAI:
    return OpenAI(
        api_key=config["deepseek"]["api_key"],
        base_url=config["deepseek"]["base_url"],
    )


def generate_mindmap(
    config: dict, source_text: str, output_dir: str
) -> dict:
    logger.info("开始生成思维导图...")

    md_path = os.path.join(output_dir, "mindmap.md")
    html_path = os.path.join(output_dir, "mindmap.html")

    if not config["deepseek"]["api_key"]:
        logger.warning("未配置 DeepSeek API Key，跳过思维导图生成")
        fallback = "# 思维导图\n\n（未配置 DeepSeek API，无法生成思维导图）"
        utils.write_text_file(md_path, fallback)
        return {"mindmap_md": md_path, "mindmap_html": None}

    system_prompt = (
        "你是一个专业的思维导图生成助手。请根据提供的文字内容生成一个"
        "Markdown 格式的思维导图。\n\n"
        "格式要求：\n"
        "1. 使用 # 表示中心主题\n"
        "2. 使用 ## 表示一级分支\n"
        "3. 使用 ### 表示二级分支\n"
        "4. 使用 - 列表表示具体要点\n"
        "5. 层级清晰，逻辑明确\n"
        "6. 内容精简，每条要点控制在20字以内\n"
        "7. 只输出 Markdown 内容，不要添加任何解释"
    )

    max_chunk_chars = config["deepseek"].get("max_chunk_minutes", 12) * 800
    if len(source_text) > max_chunk_chars * 2:
        source_text = source_text[: max_chunk_chars * 2]
        logger.info(f"文字稿较长，截取前 {max_chunk_chars * 2} 字符用于思维导图生成")

    user_content = f"请根据以下内容生成思维导图：\n\n{source_text}"
    mindmap_md = _call_deepseek(config, system_prompt, user_content)
    utils.write_text_file(md_path, mindmap_md)

    html_content = _render_mindmap_html(mindmap_md)
    utils.write_text_file(html_path, html_content)

    logger.info(f"思维导图已保存: {md_path}, {html_path}")
    return {"mindmap_md": md_path, "mindmap_html": html_path}


def _render_mindmap_html(markdown_content: str) -> str:
    lines = markdown_content.strip().split("\n")
    html_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("### "):
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("# "):
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("- "):
            html_lines.append(f"<li>{stripped[2:]}</li>")
        elif stripped.startswith("-"):
            html_lines.append(f"<li>{stripped[1:]}</li>")
        else:
            html_lines.append(f"<p>{stripped}</p>")

    html_content = "\n".join(html_lines)

    in_list = False
    result_lines = []
    for line in html_content.split("\n"):
        if line.startswith("<li>"):
            if not in_list:
                result_lines.append("<ul>")
                in_list = True
            result_lines.append(line)
        else:
            if in_list:
                result_lines.append("</ul>")
                in_list = False
            result_lines.append(line)
    if in_list:
        result_lines.append("</ul>")

    return MINDMAP_HTML_TEMPLATE.replace("{mindmap_content}", "\n".join(result_lines))


def _call_deepseek(
    config: dict,
    system_prompt: str,
    user_content: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    import time
    client = _create_client(config)
    max_retries = config["deepseek"].get("max_retries", 3)
    retry_delay = config["deepseek"].get("retry_delay_seconds", 5)

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=config["deepseek"]["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"DeepSeek API 调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
            else:
                logger.error(f"DeepSeek API 调用最终失败")
                raise
