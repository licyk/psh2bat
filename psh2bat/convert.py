"""代码转换工具"""

import re

from psh2bat.utils import generate_random_string


def psh_to_bat_code(code: str) -> str:
    """将 PowerShell 代码嵌入到 Batch 脚本代码中

    Args:
        code (str): PowerShell 脚本代码
    Returns:
        str: Batch 脚本代码
    """

    def _generate_unique_flag(base_name: str) -> str:
        flag = f"__{base_name}_{generate_random_string()}__"
        while flag in code:
            flag = f"__{base_name}_{generate_random_string()}__"
        return flag

    psh_exec_flag = _generate_unique_flag("PowerShellCodeExec")
    psh_code_flag = _generate_unique_flag("PowerShellCode")
    psh_code_args_flag = _generate_unique_flag("POWERSHELL_CODE_ARG")
    content = r"""
@echo off
@setlocal DisableDelayedExpansion
set "_bat_file_path_=%~f0"
set "_bat_file_path_p_=%_bat_file_path_:'=''%"
set "_work_path_=%~dp0"
set "{{POWERSHELL_CODE_ARGS_FLAG}}=%*"
if "%_work_path_:~-1%"=="\" set "_work_path_=%_work_path_:~0,-1%"
cmd /c "powershell -ExecutionPolicy Bypass -nop -c ""$f = [System.IO.File]::ReadAllText('%_bat_file_path_p_%') -split ':{{POWERSHELL_CODE_EXEC_FLAG}}\:.*'; . ([scriptblock]::Create($f[1])) -BatchPath '%_bat_file_path_p_%'" "
if !errorlevel!==0 (
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
        .replace("{{POWERSHELL_CODE}}", code)
        .strip()
    )

    return content


def find_powershell_exec_markers(text: str) -> list[str]:
    """使用正则表达式查找文本中的 PowerShell 执行标记

    Args:
        text (str): 要搜索的文本

    Returns:
        list[str]: 匹配到的所有标记列表
    """
    # 正则表达式模式: :__PowerShellCode_<随机字符序列>__:
    # [^:]* 表示任意数量的非冒号字符
    pattern = r":__PowerShellCode_[^:]*__:"
    matches = re.findall(pattern, text)
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

    return code.split(markers[0])[1].strip()
