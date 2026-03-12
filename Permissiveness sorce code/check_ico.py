from PIL import Image

ico = Image.open("assets/images/ico4.ico")
print(f"Основной размер: {ico.size}")
print(f"Формат: {ico.format}")

# Проверяем все размеры внутри .ico
try:
    sizes = []
    i = 0
    while True:
        ico.seek(i)
        sizes.append(ico.size)
        i += 1
except EOFError:
    pass

print(f"\nВсего размеров внутри .ico: {len(sizes)}")
print(f"Размеры: {sizes}")
