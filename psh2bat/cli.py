"""命令行参数解析工具"""

import argparse

from psh2bat.utils import normalized_filepath


def get_args_parser() -> argparse.ArgumentParser:
    """获取命令行参数

    Returns:
        argparse.ArgumentParser: 命令行参数解析器
    """

    parser = argparse.ArgumentParser(description="PowerShell 脚本转换为 Bat 脚本的工具")
    parser.add_argument("input_path", type=normalized_filepath, help="读取的 PowerShell 脚本文件路径 (使用 --reverse 参数时则为 Bat 脚本文件的路径)")
    parser.add_argument("--output-path", type=normalized_filepath, help="保存的 Bat 脚本路径")
    parser.add_argument("--executable", type=str, default=None, help="指定执行 PowerShell 脚本的解释器")
    parser.add_argument("--reverse", action="store_true", help="将输入的 Bat 脚本提取出 PowerShell 脚本")
    parser.add_argument("--version", action="store_true", help="显示版本信息")
    return parser
