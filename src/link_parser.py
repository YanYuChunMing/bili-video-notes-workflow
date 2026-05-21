import re
import logging

logger = logging.getLogger(__name__)

BILIBILI_URL_PATTERNS = [
    re.compile(
        r"https?://(?:www\.)?bilibili\.com/video/(?:av\d+|BV[\w]+)"
        r"(?:\?[^\s]*)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"https?://b23\.tv/[\w]+(?:/[^?\s]*)?(?:\?[^\s]*)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"https?://(?:www\.)?bilibili\.com/bangumi/play/(?:ep\d+|ss\d+)"
        r"(?:\?[^\s]*)?",
        re.IGNORECASE,
    ),
]

GENERAL_URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def extract_bilibili_urls(text: str) -> list[str]:
    urls = []
    for pattern in BILIBILI_URL_PATTERNS:
        matches = pattern.findall(text)
        urls.extend(matches)

    seen = set()
    unique_urls = []
    for url in urls:
        url_clean = url.rstrip(".,;:!?）)】]")
        if url_clean not in seen:
            seen.add(url_clean)
            unique_urls.append(url_clean)

    return unique_urls


def extract_all_urls(text: str) -> list[str]:
    matches = GENERAL_URL_PATTERN.findall(text)
    seen = set()
    unique_urls = []
    for url in matches:
        url_clean = url.rstrip(".,;:!?）)】]")
        if url_clean not in seen:
            seen.add(url_clean)
            unique_urls.append(url_clean)
    return unique_urls


def parse_links_file(filepath: str, bilibili_only: bool = True) -> list[str]:
    logger.info(f"读取链接文件: {filepath}")
    urls = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line:
                    continue
                if line.startswith("#"):
                    continue

                if bilibili_only:
                    found = extract_bilibili_urls(line)
                else:
                    found = extract_all_urls(line)

                if found:
                    urls.extend(found)
                    logger.debug(f"第{line_num}行: 提取到 {len(found)} 个链接")
                else:
                    logger.debug(f"第{line_num}行: 未识别到有效链接，跳过")

    except FileNotFoundError:
        logger.error(f"链接文件不存在: {filepath}")
        raise
    except Exception as e:
        logger.error(f"读取链接文件失败: {e}")
        raise

    logger.info(f"共提取 {len(urls)} 个视频链接")
    return urls
