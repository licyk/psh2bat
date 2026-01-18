"""代码转换工具"""

import re
from typing import Any

from psh2bat.utils import generate_random_string
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


def psh_to_bat_code(code: str, executable: str | None = None) -> str:
    """将 PowerShell 代码嵌入到 Batch 脚本代码中

    Args:
        code (str): PowerShell 脚本代码
        executable (str | None): 默认执行代码的 PowerShell 脚本解释器
    Returns:
        str: Batch 脚本代码
    """

    def _generate_unique_flag(base_name: str) -> str:
        flag = f"__{base_name}_{generate_random_string()}__"
        while flag in code:
            flag = f"__{base_name}_{generate_random_string()}__"
        logger.debug("'%s' 对应的替换值: '%s'", base_name, flag)
        return flag

    psh_exec_flag = _generate_unique_flag("PowerShellCodeExec")
    psh_code_flag = _generate_unique_flag("PowerShellCode")
    psh_code_args_flag = _generate_unique_flag("POWERSHELL_CODE_ARG")
    bat_file_path_flag = _generate_unique_flag("BatFilePath")
    bat_file_path_p_flag = _generate_unique_flag("BatFilePathP")
    work_path_flag = _generate_unique_flag("WorkPath")
    default_psh_executable_flag = _generate_unique_flag("DefaultPowerShellExecutable")
    psh_executable_flag = _generate_unique_flag("PowerShellExecutable")
    content = r"""
@echo off
@setlocal DisableDelayedExpansion
set "{{BatFilePath}}=%~f0"
set "{{BatFilePathP}}=%{{BatFilePath}}:'=''%"
set "{{WorkPath}}=%~dp0"
set "{{POWERSHELL_CODE_ARGS_FLAG}}=%*"
if "%{{WorkPath}}:~-1%"=="\" set "{{WorkPath}}=%{{WorkPath}}:~0,-1%"
set "BAT_SCRIPT_ROOT=%{{WorkPath}}%"
set "{{DefaultPowerShellExecutable}}={{DefaultPowerShellExecutableVal}}"
if "%{{DefaultPowerShellExecutable}}%" == "" (
    where powershell >nul 2>1
    if %ERRORLEVEL% == 0 (
        set "{{PowerShellExecutable}}=powershell"
        goto :ExecCode
    )
    where pwsh >nul 2>1
    if %ERRORLEVEL% == 0 (
        set "{{PowerShellExecutable}}=pwsh"
        goto :ExecCode
    )
) else (
    set "{{PowerShellExecutable}}=%{{DefaultPowerShellExecutable}}%"
)
:ExecCode
if "%{{PowerShellExecutable}}%" == "" (
    echo PowerShell Executable Not Found
    pause
    set "_psh_exit_code_=1"
    goto :ExitCode
)
cmd /c " "%{{PowerShellExecutable}}%" -ExecutionPolicy Bypass -nop -c ""$f = [System.IO.File]::ReadAllText('%{{BatFilePathP}}%') -split ':{{POWERSHELL_CODE_EXEC_FLAG}}\:.*'; try { . ([scriptblock]::Create($f[1])) -BatchPath '%{{BatFilePathP}}%' } catch { $_; exit 1 } " "
if %ERRORLEVEL% == 0 (
    set "_psh_exit_code_=0"
) else (
    set "_psh_exit_code_=1"
)
goto :ExitCode

:{{POWERSHELL_CODE_EXEC_FLAG}}:
param (
    [string]$BatchPath,
    [Parameter(ValueFromRemainingArguments=$true)]$ExtraArgs
)

function Get-ExtraArgs-From-Env {
    if ([string]::IsNullOrEmpty($Env:{{POWERSHELL_CODE_ARGS_FLAG}})) {
        return @()
    }
    $launch_args = $Env:{{POWERSHELL_CODE_ARGS_FLAG}}
    $arguments = [regex]::Matches($launch_args, '("[^"]*"|''[^'']*''|\S+)') | ForEach-Object {
        $_.Value -replace '^["'']|["'']$', ''
    }
    return $arguments
}

function Get-ExtraArgs {
    param (
        [string[]]$ExcludeArgs = @("-CommandWithArgs")
    )
    $extra_args = New-Object System.Collections.ArrayList

    foreach ($a in $ExtraArgs) {
        if (!($a -in $ExcludeArgs)) {
            $extra_args.Add($a) | Out-Null
        }
    }

    if ($extra_args.Count -eq 0) {
        $extra_args = Get-ExtraArgs-From-Env
    }

    $params = $extra_args.ForEach{ 
        if ($_ -match '\s|"') { "'{0}'" -f ($_ -replace "'", "''") } 
        else { $_ } 
    } -join ' '

    return $params
}

function Get-PowerShell-Code {
    param (
        [string]$ScriptPath,
        [string]$Prefix = "{{POWERSHELL_CODE_FLAG}}"
    )
    $f = [System.IO.File]::ReadAllText($ScriptPath) -split ":${Prefix}\:.*"
    return $([scriptblock]::Create($f[1]))
}

function New-RandomName {
    param(
        [ValidateRange(4, 32)]
        [int]$Length = 32
    )

    ([guid]::NewGuid().ToString("N")).Substring(0, $Length)
}

function New-TemporaryDirectory {
    param(
        [ValidateRange(4, 32)]
        [int]$NameLength = 32
    )

    do {
        $name = New-RandomName -Length $NameLength
        $path = Join-Path ([IO.Path]::GetTempPath()) $name
    } until (-not (Test-Path $path))

    New-Item -ItemType Directory -Path $path | Out-Null

    $obj = [pscustomobject]@{ Path = $path }
    $obj | Add-Member ScriptMethod Dispose {
        if (Test-Path $this.Path) {
            Remove-Item $this.Path -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    return $obj
}

function New-TemporaryFile {
    param(
        [string]$Extension = ".tmp",
        [switch]$Open,
        [ValidateRange(4, 32)]
        [int]$NameLength = 32
    )

    do {
        $name = (New-RandomName -Length $NameLength) + $Extension
        $path = Join-Path ([IO.Path]::GetTempPath()) $name
    } until (-not (Test-Path $path))

    if ($Open) {
        $fs = [IO.File]::Open(
            $path,
            [IO.FileMode]::CreateNew,
            [IO.FileAccess]::ReadWrite,
            [IO.FileShare]::None
        )
    }
    else {
        New-Item -ItemType File -Path $path | Out-Null
        $fs = $null
    }

    $obj = [pscustomobject]@{
        Path   = $path
        Stream = $fs
    }

    $obj | Add-Member ScriptMethod Dispose {
        if ($this.Stream) { $this.Stream.Dispose() }
        if (Test-Path $this.Path) {
            Remove-Item $this.Path -Force -ErrorAction SilentlyContinue
        }
    }

    return $obj
}

function Main {
    $tmp = New-TemporaryDirectory -NameLength 8
    $temp_script_name = "$(New-RandomName -NameLength 8).ps1"
    $temp_script_path = (Join-Path $tmp.Path $temp_script_name)
    $psh_script_encoding = if ($PSVersionTable.PSVersion.Major -le 5) { "UTF8" } else { "utf8BOM" }
    try {
        $psh_code = Get-PowerShell-Code -ScriptPath $BatchPath -Prefix "{{POWERSHELL_CODE_FLAG}}"
        Set-Content -Value $psh_code -Path $temp_script_path -Encoding $psh_script_encoding -Force
        $Env:{{BatFilePath}} = $null
        $Env:{{BatFilePathP}} = $null
        $Env:{{WorkPath}} = $null
        $Env:{{POWERSHELL_CODE_ARGS_FLAG}} = $null
        $Env:{{DefaultPowerShellExecutable}} = $null
        $Env:{{PowerShellExecutable}} = $null
        Invoke-Expression "& `"$temp_script_path`" $(Get-ExtraArgs)"
    }
    finally {
        $tmp.Dispose()
    }
}

Main
:{{POWERSHELL_CODE_EXEC_FLAG}}:

:{{POWERSHELL_CODE_FLAG}}:
{{POWERSHELL_CODE}}
:{{POWERSHELL_CODE_FLAG}}:


:ExitCode
exit /b %_psh_exit_code_%
"""
    content = (
        content.replace("{{POWERSHELL_CODE_EXEC_FLAG}}", psh_exec_flag)
        .replace("{{POWERSHELL_CODE_FLAG}}", psh_code_flag)
        .replace("{{POWERSHELL_CODE_ARGS_FLAG}}", psh_code_args_flag)
        .replace("{{BatFilePath}}", bat_file_path_flag)
        .replace("{{BatFilePathP}}", bat_file_path_p_flag)
        .replace("{{WorkPath}}", work_path_flag)
        .replace("{{DefaultPowerShellExecutable}}", default_psh_executable_flag)
        .replace("{{PowerShellExecutable}}", psh_executable_flag)
        .replace("{{DefaultPowerShellExecutableVal}}", executable if executable is not None else "")
        .replace("{{POWERSHELL_CODE}}", code)
        .strip()
    )

    # 此时的 PSScriptRoot 变量无法正确表示当前路径, 需要替换为 $Env:BAT_SCRIPT_ROOT
    return replace_ps_root_to_env(content)


def find_powershell_exec_markers(text: str) -> list[str]:
    """使用正则表达式查找文本中的 PowerShell 代码标记

    Args:
        text (str): 要搜索的文本

    Returns:
        list[str]: 匹配到的所有标记列表
    """
    # 正则表达式模式: :__PowerShellCode_<随机字符序列>__:
    # [^:]* 表示任意数量的非冒号字符
    pattern = r":__PowerShellCode_[^:]*__:"
    matches = re.findall(pattern, text)
    logger.debug("查找到的 PowerShell 代码标记: %s", matches)
    return matches


def extract_psh_code_from_bat(code: str) -> str | None:
    """从 Bat 脚本代码中提取 PowerShell 脚本

    Args:
        code (str): Bat 脚本代码字符串

    Returns:
        (str | None): 如果找到嵌入 Bat 脚本的 PowerShell 代码则返回其字符串, 否则返回 None
    """
    markers = find_powershell_exec_markers(code)
    if not markers:
        return None

    # 将 $Env:BAT_SCRIPT_ROOT 还原回的 PSScriptRoot 变量
    return replace_env_to_ps_root(code.split(markers[0])[1].strip())


def replace_ps_root_to_env(text: str) -> str:
    """将 $PSScriptRoot 替换为 $Env:BAT_SCRIPT_ROOT, 跳过单引号和反引号转义

    Args:
        text: 原始代码字符串
    Returns:
        str: 替换后的字符串
    """
    # 模式说明:
    # 1. ('.*?') : 匹配单引号字符串 (捕获组1)
    # 2. (`\$\{.*?\}`|`\$\w+): 匹配反引号转义的变量 (捕获组2)
    # 3. \$\{(?:(\w+):)?PSScriptRoot\} : 匹配带花括号的变量 (捕获组3)
    # 4. \$(?:(\w+):)?PSScriptRoot\b : 匹配普通变量 (捕获组4)
    pattern = r"('.*?')|(`\$(?:\{.*?\})?|`\$\w+)|(\$\{(?:\w+:)?PSScriptRoot\})|(\$(?:\w+:)?PSScriptRoot\b)"

    def subst(match: re.Match) -> Any:
        # 如果是单引号字符串或转义字符, 原样返回
        if match.group(1) or match.group(2):
            return match.group(0)
        # 如果是带花括号的格式
        if match.group(3):
            return "${Env:BAT_SCRIPT_ROOT}"
        # 如果是不带花括号的格式
        if match.group(4):
            return "$Env:BAT_SCRIPT_ROOT"
        return match.group(0)

    return re.sub(pattern, subst, text, flags=re.DOTALL)


def replace_env_to_ps_root(text: str) -> str:
    """将 $Env:BAT_SCRIPT_ROOT 还原为 $PSScriptRoot, 跳过单引号和反引号转义

    Args:
        text: 原始代码字符串
    Returns:
        str: 替换后的字符串
    """
    # 模式说明:
    # 1. ('.*?') : 匹配单引号字符串
    # 2. (`\$\{.*?\}`|`\$\w+): 匹配反引号转义
    # 3. \$\{Env:BAT_SCRIPT_ROOT\} : 目标带括号格式
    # 4. \$Env:BAT_SCRIPT_ROOT\b : 目标普通格式
    pattern = r"('.*?')|(`\$(?:\{.*?\})?|`\$\w+)|(\$\{Env:BAT_SCRIPT_ROOT\})|(\$Env:BAT_SCRIPT_ROOT\b)"

    def subst(match: re.Match) -> Any:
        if match.group(1) or match.group(2):
            return match.group(0)
        if match.group(3):
            return "${PSScriptRoot}"
        if match.group(4):
            return "$PSScriptRoot"
        return match.group(0)

    return re.sub(pattern, subst, text, flags=re.DOTALL)
