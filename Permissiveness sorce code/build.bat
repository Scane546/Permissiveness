@echo off
chcp 65001 >nul
echo ===============================================================
echo   Sborka Permissiveness
echo ===============================================================
echo.

echo [1/3] Ochistka starykh faylov sborki...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"

echo [2/3] Sborka prilozheniya s PyInstaller...
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
    main.py

if errorlevel 1 (
    echo.
    echo OSHIBKA: Sborka ne udalas!
    pause
    exit /b 1
)

echo [3/3] Kopirovanie v tselevuyu papku...
set "TARGET_DIR=C:\Users\Scane\Desktop\Permissiveness"

if not exist "%TARGET_DIR%\assets\images" mkdir "%TARGET_DIR%\assets\images"
copy /Y "dist\Permissiveness.exe" "%TARGET_DIR%\"
xcopy /Y /I "assets\images\*.*" "%TARGET_DIR%\assets\images\"
copy /Y "config.json" "%TARGET_DIR%\"
copy /Y "processes_to_kill.txt" "%TARGET_DIR%\"

echo [4/4] Ochistka vremennykh faylov...
rmdir /s /q "dist"
rmdir /s /q "build"
del /q "*.spec"

echo.
echo ===============================================================
echo   Sborka zavershena uspeshno!
echo ===============================================================
echo.
echo Fayly nakhodyatsya v papke: %TARGET_DIR%\
echo Glavnyy fayl: %TARGET_DIR%\Permissiveness.exe
echo.
pause
