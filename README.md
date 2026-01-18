# Psh2Bat
- [Psh2Bat](#psh2bat)
- [简介](#简介)
- [安装](#安装)
- [使用](#使用)
  - [PowerShell 转 Bat](#powershell-转-bat)
  - [Bat 转 PowerShell](#bat-转-powershell)
- [实现原理](#实现原理)
  - [1. 生成混合脚本](#1-生成混合脚本)
  - [2. 执行流程](#2-执行流程)
- [许可证](#许可证)

***

# 简介
将 PowerShell 脚本转换为 Bat 脚本的工具。

~~因为不想写 Bat 脚本所以写了这个工具。~~


# 安装
确保您的系统已安装 [Python](https://www.python.org) 3.10+。

```bash
pip install psh2bat
```


# 使用

## PowerShell 转 Bat
```bash
psh2bat <Bat 脚本路径> --output-path <导出路径>
```


## Bat 转 PowerShell
```bash
psh2bat <PowerShell 脚本路径> --output-path <导出路径> --reverse
```

>[!IMPORTANT]  
>仅支持由 Psh2Bat 转换而来的 Bat 脚本。


# 实现原理
Psh2Bat 并非将 PowerShell 脚本的语法逐行翻译成等效的 Batch (CMD) 语法，而是采用了一种更为巧妙的“嵌入式”打包策略。它生成一个独立的 `.bat` 文件，该文件内部包含了原始的 PowerShell 脚本，并通过一系列步骤来调用 `powershell.exe` 执行它。


## 1. 生成混合脚本
当转换一个 `.ps1` 脚本时，工具会：

1. **读取原始脚本**：将 PowerShell 脚本的全部内容读取为字符串。
2. **构建模板**：Psh2Bat 内部有一个预定义的 `.bat` 脚本模板。此模板是一个“三段式”结构，同时包含了 Batch 启动代码、一个 PowerShell 引导程序和用于注入用户脚本的占位符。不同的部分由独特的随机标记（例如 `:__PowerShellCodeExec_...__:`）分隔，以避免冲突。
3. **注入代码**：将用户原始的 PowerShell 代码注入到模板的指定位置。

最终生成的 `.bat` 文件结构如下：

```batch
@echo off
:: 第一部分：Batch 启动代码
:: ...
:: 核心是调用 powershell.exe，读取并执行文件自身的第二部分
cmd /c "powershell -ExecutionPolicy Bypass ... [scriptblock]::Create($f[1]) ..."
goto :ExitCode

:__PowerShellCodeExec_...__:
# 第二部分：PowerShell 引导代码
# ...
# 它的任务是从本文件中提取出第三部分（用户脚本）
# ...
# 然后将其写入一个临时的 .ps1 文件
Set-Content -Value $psh_code -Path $temp_script_path
# 最后执行这个临时脚本
Invoke-Expression "& `"$temp_script_path`" $(Get-ExtraArgs)"
# ...

:__PowerShellCode_...__:
# 第三部分：用户原始的 PowerShell 脚本被注入于此
# ...
:__PowerShellCode_...__:

:ExitCode
exit /b %_psh_exit_code_%
```


## 2. 执行流程
当用户运行这个生成的 `.bat` 文件时：

1. **Batch 启动**：文件顶部的 Batch 代码首先被执行。
2. **调用引导程序**：Batch 代码通过 `powershell.exe` 执行嵌入在文件第二部分的 PowerShell “引导程序”。
3. **提取并执行主脚本**：引导程序从文件自身提取出第三部分的“主脚本”（即用户原始的 PowerShell 代码），将其写入一个临时 `.ps1` 文件，然后执行这个临时文件。所有传递给 `.bat` 的命令行参数也会被完整地传递给这个临时脚本。
4.  **清理**：脚本执行完毕后，引导程序会自动删除所有临时文件，清理执行环境。


# 许可证
- [GPL-3.0](LICENSE)
