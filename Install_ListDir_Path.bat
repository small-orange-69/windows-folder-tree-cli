@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ESC 转义字符，用于ANSI颜色
for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RED=!ESC![1;31m"
set "GREEN=!ESC![1;32m"
set "YELLOW=!ESC![1;33m"
set "WHITE_BOLD=!ESC![1;37m"
set "GRAY=!ESC![90m"
set "RESET=!ESC![0m"

:: ========== 基础变量初始化 ==========
set "TARGET_DIR=%~dp0"
if "%TARGET_DIR:~-1%"=="\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"
set "BACKUP_FOLDER=!TARGET_DIR!\Path Backup"
set "REG_KEY=HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
set "REG_KEY_PS=HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
set "ARG=%~1"
set "ARG2=%~2"
set "MODE="
set "AUTO_DELETE=0"

:: ========== 参数分支：有参数直接执行，无参数进入交互式菜单 ==========
if not "%ARG%"=="" goto ArgMode

:: ===================== 交互式菜单界面（仅双击运行显示） =====================
:Menu
cls
echo !WHITE_BOLD!==============================================================!RESET!
echo !WHITE_BOLD!         List 目录树工具 — 系统PATH安装管理【安全增强版】!RESET!
echo  功能：将本工具目录加入系统PATH，CMD任意位置直接执行命令: list
echo !WHITE_BOLD!==============================================================!RESET!
echo  工具目录路径：%TARGET_DIR%
echo.
echo 【1】自动判断模式：已存在则移除，不存在则添加到系统PATH
echo 【2】安装：添加本文件夹至系统PATH环境变量
echo 【3】移除：从系统PATH删除本文件夹
echo 【4】取消，直接退出脚本
echo !WHITE_BOLD!==============================================================!RESET!
set /p "sel=请输入选项数字，按下回车确认："

if "!sel!"=="1" (
    set "MODE=AUTO"
    goto CheckAdmin
) else if "!sel!"=="2" (
    set "MODE=ADD"
    goto CheckAdmin
) else if "!sel!"=="3" (
    set "MODE=REMOVE"
    goto CheckAdmin
) else if "!sel!"=="4" (
    echo 已退出PATH管理脚本。
    pause
    exit /b 0
) else (
    echo !RED!❌ 无效输入，请重新选择菜单选项！!RESET!
    timeout /t 1 >nul
    goto Menu
)

:: ===================== 命令行参数调用入口 =====================
:ArgMode
if /i "%ARG%"=="install" (
    set "MODE=ADD"
    if /i "%ARG2%"=="autodelete" set "AUTO_DELETE=1"
    goto CheckAdmin
)
if /i "%ARG%"=="remove" set "MODE=REMOVE" & goto CheckAdmin
if /i "%ARG%"=="auto" set "MODE=AUTO" & goto CheckAdmin
echo !RED!❌ 传入参数无效！!RESET!
echo 支持调用参数：
echo    Install‑ListDir‑Path.bat install         # 添加目录进PATH，保留脚本
echo    Install‑ListDir‑Path.bat install autodelete # 添加成功后自动删除脚本自身
echo    Install‑ListDir‑Path.bat remove          # 从PATH移除目录
echo    Install‑ListDir‑Path.bat auto            # 自动判断添加/移除
pause
exit /b 1

:: ===================== 管理员权限校验（修改系统PATH必须） =====================
:CheckAdmin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo !RED!❌ 需要【管理员权限】才能修改系统环境变量PATH！!RESET!
    echo 请右键本bat脚本，选择「以管理员身份运行」。
    pause
    exit /b 1
)

echo.
echo !WHITE_BOLD!==============================================================!RESET!
echo 目标工具目录：%TARGET_DIR%
echo 当前执行模式：%MODE%
echo !WHITE_BOLD!==============================================================!RESET!
echo.

:: ===================== 步骤1：生成注册表备份（放入Path Backup子文件夹） =====================
echo [1/4] 正在准备PATH备份目录...
if not exist "!BACKUP_FOLDER!" (
    mkdir "!BACKUP_FOLDER!"
    echo  创建备份目录：!BACKUP_FOLDER!
)
echo [1/4] 正在备份系统PATH注册表项...
for /f "delims=" %%a in ('powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'"') do set "TIMESTAMP=%%a"
set "BACKUP_FILE=!BACKUP_FOLDER!\Path_Backup_!TIMESTAMP!.reg"
reg export "%REG_KEY%" "%BACKUP_FILE%" >nul
if !errorlevel! equ 0 (
    echo !GREEN!✅ 备份完成：!BACKUP_FILE!!RESET!
) else (
    echo !RED!❌ 注册表备份失败！操作终止，防止数据丢失。!RESET!
    pause
    exit /b 1
)
echo.

:: ===================== 步骤2：PowerShell读取PATH，预览变更 =====================
echo [2/4] 读取当前PATH并计算变更预览...
echo.
set "TMP_PREVIEW=%temp%\path_preview.tmp"
powershell -NoProfile -Command "$regPath='%REG_KEY_PS%';$targetDir='%TARGET_DIR%';$mode='%MODE%';$raw=(Get-ItemProperty $regPath -Name Path).Path;$arr = $raw -split ';' | Where-Object {$_ -ne ''};$exists = ($arr | Where-Object {$_ -ieq $targetDir}) -ne $null;$newArr = $arr | Where-Object {$_ -ine $targetDir};if($mode -eq 'ADD'){$newArr += $targetDir}elseif($mode -eq 'AUTO'){if($exists){$newArr = $arr | Where-Object {$_ -ine $targetDir}}else{$newArr += $targetDir}};Write-Host 'EXISTS:'$exists;Write-Host '===== 变更后PATH条目列表 =====';$newArr | ForEach-Object { Write-Host $_ };" > "!TMP_PREVIEW!"

:: 解析预览输出
findstr /i "EXISTS:" "!TMP_PREVIEW!" > "%temp%\exist_flag.tmp"
for /f "tokens=1,2 delims=:" %%a in (%temp%\exist_flag.tmp) do set "PATH_EXIST=%%b"

echo 目标路径在当前系统PATH中：!PATH_EXIST!
echo.
:: 打印预览内容，跳过EXISTS那一行
for /f "skip=1 delims=" %%l in (!TMP_PREVIEW!) do echo %%l
echo.

:: ===================== 步骤3：用户确认环节 =====================
set /p "confirm=!YELLOW!⚠️ 确认执行本次PATH修改？输入 Y 确认，其他字符取消操作：!RESET!"
if /i not "!confirm!"=="Y" (
    echo.
    echo !RED!❌ 用户取消操作，脚本退出。备份文件保留：!BACKUP_FILE!!RESET!
    pause
    exit /b 0
)
echo.

:: ===================== 步骤4：PowerShell执行写入PATH =====================
echo [3/4] 正在写入新PATH到注册表...
powershell -NoProfile -Command "$regPath='%REG_KEY_PS%';$targetDir='%TARGET_DIR%';$mode='%MODE%';$raw=(Get-ItemProperty $regPath -Name Path).Path;$arr = $raw -split ';' | Where-Object {$_ -ne ''};$newArr = $arr | Where-Object {$_ -ine $targetDir};if($mode -eq 'ADD'){$newArr += $targetDir}elseif($mode -eq 'AUTO'){$exists = ($arr | Where-Object {$_ -ieq $targetDir}) -ne $null;if($exists){$newArr = $arr | Where-Object {$_ -ine $targetDir}}else{$newArr += $targetDir}};$newStr = $newArr -join ';';if($newStr.Length -gt 4000){throw 'PATH总长度超过4000字符，拒绝写入！'};Set-ItemProperty -Path $regPath -Name Path -Value $newStr -Type ExpandString;"

set "PS_RET=%errorlevel%"
if !PS_RET! equ 0 (
    echo !GREEN!✅ PATH注册表写入成功！!RESET!
) else (
    echo !RED!❌ PowerShell执行失败，PATH未修改！!RESET!
    echo 备份文件仍在：!BACKUP_FILE!
    pause
    exit /b 1
)
echo.

:: ===================== 自删逻辑（仅install autodelete模式） =====================
if !AUTO_DELETE! equ 1 (
    echo [4/4] 安装完成，2秒后自动删除脚本本体...
    ping -n 2 127.0.0.1 >nul
    del "%~f0" >nul 2>&1
)

:FinishTip
echo.
echo !YELLOW!⚠️ 【重要生效提示】!RESET!
echo    环境变量已经写入注册表，已经打开的CMD窗口不会自动刷新
echo    请全部关闭CMD/PowerShell，重新打开终端。
echo.
echo 📌 使用示例（新开终端后，直接执行 list 命令）：
echo !GRAY!   list                  直接打印当前目录树!RESET!
echo !GRAY!   list 3                限制扫描深度为3!RESET!
echo !GRAY!   list set              打开配置菜单!RESET!
echo !GRAY!   list help             查看全部帮助文档!RESET!
echo !GRAY!   list -depth 2 -debug true   带参数运行!RESET!
echo.
echo 📌 安全备份：本次修改前已生成注册表备份文件
echo    !BACKUP_FILE!
echo    一旦PATH异常，双击该.reg文件即可恢复旧PATH。
echo.
pause
endlocal
