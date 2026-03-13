@echo off
chcp 65001 >nul
echo ===============================================================
echo   Оптимизированная сборка Permissiveness
echo ===============================================================
echo.

echo [1/5] Прекомпиляция Python файлов...
python precompile.py
if errorlevel 1 (
    echo.
    echo ОШИБКА: Прекомпиляция не удалась!
    pause
    exit /b 1
)

echo [2/5] Очистка старых файлов сборки...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"

echo [3/5] Сборка приложения с PyInstaller (оптимизированная)...
pyinstaller --noconfirm --onefile --windowed ^
    --name "Permissiveness" ^
    --icon "assets\images\ico4.ico" ^
    --add-data "assets\images\ico4.ico;assets\images" ^
    --add-data "assets\images\icon.ico;assets\images" ^
    --add-data "assets\images\logo.png;assets\images" ^
    --add-data "assets\images\Portal  WG ico.png;assets\images" ^
    --add-data "assets\images\Zapret.bat.png;assets\images" ^
    --add-data "assets\images\Zapret2.ico;assets\images" ^
    --add-data "config.json;." ^
    --add-data "processes_to_kill.txt;." ^
    --hidden-import "app_info" ^
    --optimize 2 ^
    --strip ^
    main.py

if errorlevel 1 (
    echo.
    echo ОШИБКА: Сборка не удалась!
    pause
    exit /b 1
)

echo [4/5] Копирование в целевую папку...
set "TARGET_DIR=C:\Users\Scane\Desktop\Permissiveness"

if not exist "%TARGET_DIR%\assets\images" mkdir "%TARGET_DIR%\assets\images"
copy /Y "dist\Permissiveness.exe" "%TARGET_DIR%\"
xcopy /Y /I "assets\images\*.*" "%TARGET_DIR%\assets\images\"
copy /Y "config.json" "%TARGET_DIR%\"
copy /Y "processes_to_kill.txt" "%TARGET_DIR%\"

echo [5/5] Очистка временных файлов...
rmdir /s /q "dist"
rmdir /s /q "build"
if exist "compiled" rmdir /s /q "compiled"
del /q "*.spec"
del /q "*.pyc"

echo.
echo ===============================================================
echo   Оптимизированная сборка завершена успешно!
echo ===============================================================
echo.
echo Файлы находятся в папке: %TARGET_DIR%\
echo Главный файл: %TARGET_DIR%\Permissiveness.exe
echo.
pause
