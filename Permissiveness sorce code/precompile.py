"""
Скрипт для прекомпиляции Python файлов в .pyc
Оптимизирует код перед сборкой в exe
"""
import py_compile
import compileall
import os
import shutil
import sys
from pathlib import Path

def precompile_files():
    """Прекомпиляция всех Python файлов в текущей директории"""
    print("=" * 60)
    print("  Прекомпиляция Python файлов")
    print("=" * 60)
    print()
    
    # Получаем текущую директорию
    current_dir = Path(__file__).parent
    
    # Список файлов для компиляции
    python_files = [
        "main.py",
        "app_info.py",
        "native_dialog.py"
    ]
    
    compiled_count = 0
    failed_count = 0
    
    print("[1/3] Компиляция отдельных файлов...")
    for py_file in python_files:
        file_path = current_dir / py_file
        if file_path.exists():
            try:
                # Компиляция с оптимизацией уровня 2
                py_compile.compile(
                    str(file_path),
                    cfile=str(file_path.with_suffix('.pyc')),
                    optimize=2,
                    doraise=True
                )
                print(f"  ✓ {py_file} -> {py_file}c")
                compiled_count += 1
            except Exception as e:
                print(f"  ✗ Ошибка при компиляции {py_file}: {e}")
                failed_count += 1
        else:
            print(f"  ⚠ Файл не найден: {py_file}")
    
    print()
    print("[2/3] Массовая компиляция директории...")
    try:
        # Компиляция всей директории с оптимизацией
        compileall.compile_dir(
            str(current_dir),
            maxlevels=1,
            optimize=2,
            quiet=1,
            legacy=False
        )
        print("  ✓ Директория скомпилирована")
    except Exception as e:
        print(f"  ✗ Ошибка при массовой компиляции: {e}")
    
    print()
    print("[3/3] Создание папки для скомпилированных файлов...")
    compiled_dir = current_dir / "compiled"
    if compiled_dir.exists():
        shutil.rmtree(compiled_dir)
    compiled_dir.mkdir()
    
    # Копируем .pyc файлы в отдельную папку
    for pyc_file in current_dir.glob("*.pyc"):
        shutil.copy2(pyc_file, compiled_dir / pyc_file.name)
        print(f"  ✓ Скопирован: {pyc_file.name}")
    
    print()
    print("=" * 60)
    print(f"  Прекомпиляция завершена!")
    print(f"  Успешно: {compiled_count} | Ошибок: {failed_count}")
    print("=" * 60)
    print()
    print(f"Скомпилированные файлы находятся в: {compiled_dir}")
    print()

if __name__ == "__main__":
    try:
        precompile_files()
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nКритическая ошибка: {e}")
        sys.exit(1)
