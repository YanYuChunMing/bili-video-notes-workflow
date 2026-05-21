import os
import logging

from openai import OpenAI

from . import utils

logger = logging.getLogger(__name__)


def _create_client(config: dict) -> OpenAI:
    return OpenAI(
        api_key=config["deepseek"]["api_key"],
        base_url=config["deepseek"]["base_url"],
    )


def generate_summary(
    config: dict, cleaned_text: str, output_path: str
) -> str:
    logger.info("开始生成学习笔记型总结...")

    if not config["deepseek"]["api_key"]:
        logger.warning("未配置 DeepSeek API Key，跳过笔记生成")
        fallback = "# 学习笔记\n\n（未配置 DeepSeek API，无法生成笔记摘要）\n\n## 原文\n\n" + cleaned_text
        utils.write_text_file(output_path, fallback)
        return fallback

    system_prompt = (
        "你是一个专业的学习笔记整理助手。请根据提供的视频文字稿，生成一份结构清晰、"
        "适合复习的学习笔记型摘要。\n\n"
        "要求：\n"
        "1. 使用 Markdown 格式\n"
        "2. 包含视频核心内容提炼和要点归纳\n"
        "3. 结构清晰，使用标题、列表等层级组织\n"
        "4. 保留课程/视频中的关键知识点、概念、步骤\n"
        "5. 如果有代码或公式，保留并格式化\n"
        "6. 不要写成营销文案风格\n"
        "7. 语言简洁、准确，便于日后复习\n"
        "8. 在末尾添加一个「关键要点」小节，列出3-7个最重要的takeaway"
    )

    max_chunk_chars = config["deepseek"].get("max_chunk_minutes", 12) * 800
    text_len = len(cleaned_text)

    if text_len <= max_chunk_chars:
        user_content = f"请根据以下视频文字稿生成学习笔记：\n\n{cleaned_text}"
        result = _call_deepseek(config, system_prompt, user_content)
    else:
        logger.info(f"文字稿较长 ({text_len} 字符)，采用分块摘要策略")
        chunks = _split_text(cleaned_text, max_chunk_chars)
        chunk_summaries = []

        for i, chunk in enumerate(chunks):
            logger.info(f"摘要第 {i + 1}/{len(chunks)} 块...")
            chunk_prompt = (
                "请为以下文字稿片段生成要点摘要，保留关键信息和知识点：\n\n"
                + chunk
            )
            chunk_summary = _call_deepseek(config, system_prompt, chunk_prompt, max_tokens=2048)
            chunk_summaries.append(chunk_summary)

        merge_content = "\n\n---\n\n".join(chunk_summaries)
        user_content = (
            "以下是视频文字稿各分块的关键要点摘要，请将它们整合成一份完整的"
            "学习笔记：\n\n" + merge_content
        )
        result = _call_deepseek(config, system_prompt, user_content)

    utils.write_text_file(output_path, result)
    logger.info(f"学习笔记已保存到: {output_path}")
    return result


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


def _split_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    paragraphs = text.split("\n")
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) + 1 > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk += ("\n" + para) if current_chunk else para
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks
