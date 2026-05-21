import os
import time
import logging

from openai import OpenAI

from . import utils

logger = logging.getLogger(__name__)


def _create_client(config: dict) -> OpenAI:
    return OpenAI(
        api_key=config["deepseek"]["api_key"],
        base_url=config["deepseek"]["base_url"],
    )


def _call_deepseek(
    config: dict,
    system_prompt: str,
    user_content: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
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


def clean_transcript_with_punctuation(
    config: dict, raw_text: str, output_path: str
) -> str:
    logger.info("开始标点补全和段落整理...")

    if not config["deepseek"]["api_key"]:
        logger.warning("未配置 DeepSeek API Key，跳过标点整理，返回原文")
        utils.write_text_file(output_path, raw_text)
        return raw_text

    system_prompt = (
        "你是一个专业的中文文字整理助手。你的任务是：\n"
        "1. 为一段没有标点符号的中文文字添加合适的标点符号（句号、逗号、问号、感叹号等）\n"
        "2. 根据语义将文字分成合理的段落\n"
        "3. 保持原文内容不变，只添加标点和分段\n"
        "4. 不要添加原文中没有的内容\n"
        "5. 不要修改原文的措辞和用词\n"
        "6. 输出格式为纯文本，不要添加任何解释或说明"
    )

    max_chunk_chars = config["deepseek"].get("max_chunk_minutes", 12) * 800
    chunks = _split_text(raw_text, max_chunk_chars)
    logger.info(f"文字稿分为 {len(chunks)} 块进行处理")

    cleaned_chunks = []
    for i, chunk in enumerate(chunks):
        logger.info(f"处理第 {i + 1}/{len(chunks)} 块...")
        user_content = f"请为以下文字添加标点符号并进行分段：\n\n{chunk}"
        cleaned = _call_deepseek(config, system_prompt, user_content)
        cleaned_chunks.append(cleaned)

    result = "\n\n".join(cleaned_chunks)
    utils.write_text_file(output_path, result)
    logger.info(f"标点整理完成，已保存到: {output_path}")
    return result


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
            if current_chunk:
                current_chunk += "\n" + para
            else:
                current_chunk = para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
