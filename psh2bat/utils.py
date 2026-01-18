"""其他"""

import string
import random
from pathlib import Path

from psh2bat.config import (
    LOGGER_NAME,
    LOGGER_LEVEL,
    LOGGER_COLOR,
)
from psh2bat.logger import get_logger


logger = get_logger(
    name=LOGGER_NAME,
    level=LOGGER_LEVEL,
    color=LOGGER_COLOR,
)


def generate_random_string(
    length: int | None = 8,
    chars: str | None = None,
    include_uppercase: bool | None = True,
    include_lowercase: bool | None = True,
    include_digits: bool | None = True,
    include_special: bool | None = False,
):
    """
    生成随机字符串

    Args:
        length (int | None): 字符串长度, 默认为 8
        chars (str | None): 自定义字符集，如果提供则忽略其他参数
        include_uppercase (bool | None): 是否包含大写字母
        include_lowercase (bool | None): 是否包含小写字母
        include_digits (bool | None): 是否包含数字
        include_special (bool | None): 是否包含特殊字符

    Returns:
        str: 生成的随机字符串
    """
    if chars is not None:
        char_pool = chars
    else:
        char_pool = ""
        if include_uppercase:
            char_pool += string.ascii_uppercase
        if include_lowercase:
            char_pool += string.ascii_lowercase
        if include_digits:
            char_pool += string.digits
        if include_special:
            char_pool += "!@#$%^&*"

    if not char_pool:
        raise ValueError("字符池不能为空")

    return "".join(random.choice(char_pool) for _ in range(length))


def is_utf8_bom_encoding_file(
    file_path: Path,
) -> bool:
    """检测文本文件是否为 UTF8 BOM 编码保存

    Args:
        file_path (Path): 文本文件路径

    Returns:
        bool: 检测结果
    """
    with open(file_path, "rb") as file:
        bom = file.read(3)
        return bom == b"\xef\xbb\xbf"


def detect_encoding(
    file_path: Path,
) -> str:
    """
    检测文件的编码格式

    Args:
        file_path (Path): 文件路径

    Returns:
        str: 检测到的编码格式, 如 'utf-8' 或 'gbk'
    """
    if is_utf8_bom_encoding_file(file_path):
        logger.debug("'%s' 文件编码格式为 UTF8 BOM", file_path)
        return "utf-8-sig"

    with open(file_path, "rb") as f:
        raw_data = f.read()

    try:
        raw_data.decode("utf-8")
        logger.debug("'%s' 文件编码格式为 UTF8", file_path)
        return "utf-8"
    except UnicodeDecodeError:
        logger.debug("'%s' 文件编码格式为 GBK", file_path)
        return "gbk"


def save_file(
    content: str | list[str],
    save_path: Path,
    encoding: str = "utf-8",
    use_crlf: bool = False,
) -> None:
    """保存文本到文件中

    Args:
        content (str | list[str]): 要保存的文本内容
        save_path (Path): 保存路径
        encoding (str): 保存编码
        use_crlf (bool): 是否使用 CRLF 换行符
    """
    if use_crlf:
        newline = "\r\n"
    else:
        newline = "\n"

    if isinstance(content, list):
        content = f"{newline}".join(content)

    with open(save_path, "w", encoding=encoding, newline=newline) as file:
        file.write(content)


def read_file(
    file_path: Path,
    encoding: str | None = None,
) -> str:
    """从文件中读取文本

    Args:
        file_path (Path): 文件路径
        encoding (str | None): 读取编码
    Returns:
        str: 读取的文本内容
    """
    if encoding is None:
        encoding = detect_encoding(file_path)

    with open(file_path, "r", encoding=encoding) as file:
        return file.read()


def normalized_filepath(
    filepath: str | Path,
) -> Path:
    """将输入的路径转换为绝对路径

    Args:
        filepath (str | Path): 原始的路径
    Returns:
        Path: 绝对路径
    """
    if filepath is not None:
        filepath = Path(filepath).absolute()

    logger.debug("解析成绝对路径后的路径: '%s'", filepath)
    return filepath
