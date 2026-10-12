@echo off
chcp 65001 > nul
title HealthAI 智慧舱 - 全量打包

echo.
echo ╔══════════════════════════════════════╗
echo ║   HealthAI 智慧舱 · 全量打包脚本      ║
echo ╚══════════════════════════════════════╝
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 激活虚拟环境
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] 虚拟环境激活失败，请检查 venv 目录。
    pause & exit /b 1
)

echo [1/4] 清理旧的构建产物...
rmdir /s /q build 2>nul
rmdir /s /q dist  2>nul
echo      完成。

echo.
echo [2/4] 打包主程序（HealthAI智慧舱.exe）...
pyinstaller healthai.spec --noconfirm
if errorlevel 1 (
    echo [ERROR] 主程序打包失败！
    pause & exit /b 1
)
echo      完成。

echo.
echo [3/4] 打包模拟器（用户2 / 用户3）...

pyinstaller --onefile --console ^
    --name "模拟传感器_用户2(管理员)" ^
    --distpath "dist_sim" ^
    simulator_user2.py
if errorlevel 1 ( echo [WARN] 用户2模拟器打包失败 )

pyinstaller --onefile --console ^
    --name "模拟传感器_用户3(居家老人)" ^
    --distpath "dist_sim" ^
    simulator_user3.py
if errorlevel 1 ( echo [WARN] 用户3模拟器打包失败 )

echo      完成。

echo.
echo [4/4] 将模拟器复制到主程序目录...
copy /Y "dist_sim\模拟传感器_用户2(管理员).exe"   "dist\HealthAI智慧舱\"
copy /Y "dist_sim\模拟传感器_用户3(居家老人).exe"  "dist\HealthAI智慧舱\"

:: 清理模拟器临时 build 目录
rmdir /s /q dist_sim  2>nul
del /q "模拟传感器_用户2(管理员).spec" 2>nul
del /q "模拟传感器_用户3(居家老人).spec" 2>nul

echo      完成。

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║  打包完成！输出目录：dist\HealthAI智慧舱\                  ║
echo ║                                                          ║
echo ║  包含文件：                                               ║
echo ║    HealthAI智慧舱.exe          主程序（双击运行）          ║
echo ║    模拟传感器_用户2(管理员).exe  模拟ID=2数据（双击运行）    ║
echo ║    模拟传感器_用户3(居家老人).exe 模拟ID=3数据（双击运行）   ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

pause
