# windows\-folder\-tree\-cli

> Generate aesthetic folder tree list inside CMD / PowerShell\.
> 在 CMD / PowerShell 快速生成美观的文件夹树状列表工具
> 
> 


## 简介 / Introduction

A Windows command\-line directory tree viewer, enhanced replacement for the system built\-in `tree` command\. After setting environment variable, run `list` in any terminal to get formatted directory tree\. Supports scan depth limit, file filter, regex match and persistent configuration\.

ListDir 是一款 Windows 命令行目录树查看工具，用来替代系统自带简陋的 `tree` 命令。配置好环境变量之后，可以在任意终端直接执行 `list` 命令，输出格式化的目录树，支持自定义扫描深度、文件后缀黑白名单、名称正则过滤、调试模式，所有配置支持持久保存。

工具包内含文件 / Included files：

- `listdir.exe`：Pre\-compiled main program, Python runtime NOT required

- `listdir.exe`：打包后的主程序，无需额外安装 Python

- `list.bat`：CLI entry wrapper script, enables calling `list` after PATH configured

- `list.bat`：命令入口包装脚本，配合 PATH 实现直接调用 `list`

- `Install-ListDir-Path.bat`：One\-click PATH environment variable install / uninstall script

- `Install-ListDir-Path.bat`：PATH 环境变量一键安装/卸载脚本

- `config.json`：User configuration file, auto\-generated on first launch

- `config.json`：程序配置文件（首次运行自动生成）

- `lang.json`：Multi\-language resource file

- `lang.json`：多语言文本资源文件

## 文件结构 / File structure

Extract all files into the same folder, do not split files apart\.

将压缩包内全部文件解压放到同一个文件夹内，不要拆分文件。

```
工具文件夹/
├─ _internal                  # Python依赖库文件夹，**必须与 listdir.exe 放在同一目录，不可拆分移动**
├─ Install-ListDir-Path.bat   # PATH environment management script / PATH 环境管理脚本
├─ list.bat                   # list command entry / list 命令入口
├─ listdir.exe                # Main executable, no Python required / 主程序（独立 exe，无需 Python）
├─ config.json                # User config (auto-generate) / 配置（首次运行自动生成）
└─ lang.json                  # Language resource / 语言资源
```

## 快速开始 / Quick start

### 1\. 配置系统 PATH（必须步骤） / Configure system PATH \(required\)

1. Right\-click `Install-ListDir-Path.bat` and select **Run as administrator**

2. 右键 `Install-ListDir-Path.bat`，选择**以管理员身份运行**

3. Select operation from menu:

4. 在弹出菜单选择操作：

    - `【1】Auto mode`：Check PATH entry, add if missing, remove if exists \(recommended\)

    - `【1】自动判断模式`：检测目录是否存在 PATH，存在就移除，不存在就添加（日常推荐）

    - `【2】Install`：Add current folder into system PATH

    - `【2】安装`：把当前工具文件夹添加进系统 PATH

    - `【3】Remove`：Remove tool folder from system PATH

    - `【3】移除`：从系统 PATH 删除工具文件夹

    - `【4】Cancel`：Exit script

    - `【4】取消`：退出脚本

> ⚠️ After modifying environment variable, **close all existing CMD/PowerShell windows and reopen terminal to take effect**\.
> 
> ⚠️ 修改环境变量完成后，**关闭全部已打开 CMD/PowerShell，重新打开终端才会生效**。
> 
> 

Command\-line arguments call \(run in administrator terminal, skip interactive menu\):

命令行参数调用方式（管理员终端内执行，跳过交互菜单）：

```cmd
Install-ListDir-Path.bat install   :: Add to system PATH / 添加到系统 PATH
Install-ListDir-Path.bat remove    :: Remove from system PATH / 从系统 PATH 移除
Install-ListDir-Path.bat auto      :: Auto add or remove / 自动判断 添加/移除
```

### 2\. 基础使用 / Basic usage

Open new terminal, change working directory to target folder and run:

新开终端，切换到你想要查看的目录，直接执行：

```cmd
list
```

Directory tree of current folder will be printed\.

即可打印当前目录的树状结构图。

## 命令行使用方式 / CLI usage

### 基础位置参数 / Positional argument

```cmd
list N
```

`N`: Number for scan depth limit\. Example `list 3` only scan 3 levels\.

`N`：数字，代表扫描目录深度；例如 `list 3`，只扫描 3 层目录。

示例 / Examples：

```cmd
list        :: Print tree with default depth / 使用配置默认深度打印目录树
list 2      :: Limit scan depth to 2 levels / 限制扫描深度为 2 层
```

### 子命令 / Sub\-commands

```cmd
list set        :: Open interactive setting menu for persistent config / 打开交互式设置菜单，修改持久化配置
list help       :: Show full help text / 查看完整帮助文本
```

### 完整可选参数（临时生效，不会保存到配置文件） / Optional arguments \(temporary, not saved to config\)

Usage format: `list -argument value`

使用格式：`list -参数名 参数值`

- `-depth`: Set max scan depth\. Range 0\-255, 0 = unlimited depth

- `-depth`：设置扫描最大深度。取值范围 0\-255，0 代表不限制深度

- `-admin`: Run with administrator privileges\. Valid: `true` / `false` / `1` / `0`

- `-admin`：是否以管理员模式运行。可选 `true` / `false` / `1` / `0`

- `-debug`: Enable debug log output\. Valid: `true` / `false` / `1` / `0`

- `-debug`：开启调试输出日志。可选 `true` / `false` / `1` / `0`

- `-maxentries`: Max items show per directory, 0 = no limit\. Range 0\-255

- `-maxentries`：单个目录最多展示条目数量，0 = 不限制。取值范围 0\-255

- `-whitelist`: File extension whitelist, split by comma\. Example `.txt,.exe,.md`

- `-whitelist`：文件后缀白名单，多个后缀使用逗号分隔，示例 `.txt,.exe,.md`

- `-blacklist`: File extension blacklist, split by comma\. Example `.exe,.log`

- `-blacklist`：文件后缀黑名单，多个后缀使用逗号分隔，示例 `.exe,.log`

- `-listmode`: File filter mode\. 1=whitelist; 2=blacklist; 3=no filter; 4=folders\-only

- `-listmode`：文件过滤模式。1 = 白名单模式；2 = 黑名单模式；3 = 不过滤；4 = 仅显示文件夹

- `-regex`: Regex pattern for filename filtering

- `-regex`：文件名称正则表达式过滤规则，填写正则字符串

- `-enableregex`: Toggle filename regex filter\. Valid: `true` / `false` / `1` / `0`

- `-enableregex`：是否启用名称正则过滤。可选 `true` / `false` / `1` / `0`

参数示例 / Argument examples：

```cmd
:: Scan depth 2 with debug enabled / 扫描深度 2，开启调试模式
list -depth 2 -debug true
:: Blacklist filter, hide exe and log files / 黑名单过滤，不显示 exe、log 文件
list -listmode 2 -blacklist .exe,.log
:: Regex filter, show exe and md files only / 使用正则过滤，只显示 exe 与 md 文件
list -enableregex true -regex "\.(exe|md)$"
```

## 设置菜单说明 / Setting menu

Run command:

执行命令：

```cmd
list set
```

Enter interactive setting menu to modify persistent options saved in `config.json`:

进入交互式设置界面，可以修改持久保存到 `config.json` 的配置：

1. Default scan depth / 默认扫描深度

2. Interface language / 界面语言

3. Request admin privilege by default / 默认是否请求管理员权限

4. Enable debug log by default / 默认是否开启调试日志

5. Max display items per directory / 单目录最大展示条目

6. File extension whitelist / 文件后缀白名单

7. File extension blacklist / 文件后缀黑名单

8. File filter mode / 文件过滤模式

9. Filename regex pattern / 文件名称正则表达式

10. Toggle filename regex filter / 是否开启正则过滤

> Input `q` inside setting menu to quit\.
> 
> 在设置菜单输入 `q` 即可退出设置界面。
> 
> 

## 使用注意事项 / Notes

1. PATH setup script **must be Run as administrator**, otherwise environment variable cannot be modified\.

2. PATH 安装脚本**必须右键以管理员身份运行**，否则无法修改系统环境变量。

3. Modified PATH will NOT take effect on already\-opened terminals, you must reopen terminal window\.

4. 修改 PATH 环境变量后，**已经打开的终端不会自动刷新，必须重新打开终端**。

5. If you move the whole tool folder, run `Install-ListDir-Path.bat remove` first to clear old PATH entry before reinstall\.

6. 如果移动整个工具文件夹，务必先执行 `Install-ListDir-Path.bat remove` 移除旧 PATH，再重新执行安装。

7. Tool works with path containing Chinese characters or spaces, but display abnormality may occur on outdated terminals\.

8. 目录路径中包含中文、空格时程序也可正常工作，但部分老旧终端环境可能会出现显示异常。

9. This is standalone pre\-built exe release, **Python runtime is NOT required**, just unzip and use\.

10. 本版本为独立打包 exe，**无需额外安装 Python 运行环境**，解压即可使用。

---

> This document is AI\-assisted and manually reviewed\.
> 
> 本文档由 AI 辅助编写，内容经过人工整理校验。
