"""Psh2Bat 转换工具"""

import sys

from psh2bat.cli import get_args_parser
from psh2bat.convert import (
    psh_to_bat_code,
    extract_psh_code_from_bat,
)
from psh2bat.config import (
    LOGGER_NAME,
    LOGGER_LEVEL,
    LOGGER_COLOR,
)
from psh2bat.logger import get_logger
from psh2bat.utils import (
    read_file,
    save_file,
)
from psh2bat.version import VERSION

logger = get_logger(
    name=LOGGER_NAME,
    level=LOGGER_LEVEL,
    color=LOGGER_COLOR,
)


def run_app() -> None:
    """工具启动入口"""
    parser = get_args_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.version:
        logger.info("Psh2Bat 版本: %s", VERSION)
        sys.exit(0)

    if not args.input_path.is_file():
        logger.error("输入的脚本路径 '%s' 不存在", args.input_path)
        sys.exit(1)

    input_path = args.input_path

    if args.output_path is not None:
        save_path = args.output_path
    else:
        if args.reverse:
            save_path = input_path.parent / f"{input_path.stem}.ps1"
        else:
            save_path = input_path.parent / f"{input_path.stem}.bat"

    code = read_file(file_path=input_path)
    if args.reverse:
        content = extract_psh_code_from_bat(code)
        if content is None:
            logger.error("未在 '%s' 中找到 PowerShell 代码, 无法将 Bat 脚本转换为 PowerShell 脚本, 可能该 Bat 脚本非本工具生成", input_path)
            sys.exit(1)

        save_file(
            content=content,
            save_path=save_path,
            encoding="utf-8-sig",
            use_crlf=False,
        )
        logger.info("Bst 脚本转换为 PowerShell 脚本: %s -> %s", input_path, save_path)
    else:
        content = psh_to_bat_code(code)
        save_file(
            content=content,
            save_path=save_path,
            encoding="utf-8",
            use_crlf=True,
        )
        logger.info("PowerShell 脚本转换为 Bat 脚本: %s -> %s", input_path, save_path)
