from PIL import Image

# Открываем исходное изображение
img = Image.open("assets/images/ico4.png")

# Конвертируем в RGBA
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Создаем все размеры
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
images = []

for size in sizes:
    resized = img.resize(size, Image.Resampling.LANCZOS)
    images.append(resized)

# Сохраняем как multi-size .ico
images[0].save(
    "assets/images/ico4_fixed.ico",
    format='ICO',
    sizes=sizes,
    append_images=images[1:]
)

print("Готово! Файл: assets/images/ico4_fixed.ico")
print("Проверь его - если норм, замени ico4.ico")
