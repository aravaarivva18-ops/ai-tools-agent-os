import os
import tempfile

import piexif
import pytest
from PIL import Image, PngImagePlugin

# Импортируем функции, которые мы планируем реализовать в clean_image_metadata
# Но поскольку файл еще не создан или не содержит их, тест упадет (RED фаза)
from tools.clean_image_metadata.clean_image_metadata import (
    clean_image,
    clean_jpeg_metadata,
    clean_png_metadata,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_clean_jpeg_metadata(temp_dir):
    # 1. Создаем временное JPEG-изображение с EXIF
    img_path = os.path.join(temp_dir, "test.jpg")
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path, "JPEG")

    # Записываем EXIF данные
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: b"TestMake",
            piexif.ImageIFD.Software: b"Stable Diffusion",
        },
        "Exif": {
            piexif.ExifIFD.UserComment: b"Created by AI Generator",
        },
    }
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, img_path)

    # Проверяем, что EXIF записался
    data = piexif.load(img_path)
    assert data["0th"].get(piexif.ImageIFD.Software) == b"Stable Diffusion"

    # 2. Очищаем метаданные
    out_path = os.path.join(temp_dir, "test_cleaned.jpg")
    success = clean_jpeg_metadata(img_path, out_path)
    assert success is True
    assert os.path.exists(out_path)

    # 3. Проверяем, что EXIF удален
    clean_data = piexif.load(out_path)
    # Пустой EXIF в piexif обычно не содержит ключей "0th" или они пустые
    assert len(clean_data["0th"]) == 0
    assert len(clean_data["Exif"]) == 0

    # Убедимся, что изображение открывается и целостность не нарушена
    with Image.open(out_path) as clean_img:
        assert clean_img.size == (100, 100)


def test_clean_png_metadata(temp_dir):
    # 1. Создаем временное PNG-изображение с текстовыми чанками (метаданными)
    img_path = os.path.join(temp_dir, "test.png")
    img = Image.new("RGBA", (100, 100), color="blue")

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Software", "NovelAI")
    metadata.add_text("parameters", "AI Prompt metadata here")
    img.save(img_path, "PNG", pnginfo=metadata)

    # Проверяем, что метаданные записались
    with Image.open(img_path) as opened_img:
        assert opened_img.info.get("Software") == "NovelAI"
        assert opened_img.info.get("parameters") == "AI Prompt metadata here"

    # 2. Очищаем метаданные
    out_path = os.path.join(temp_dir, "test_cleaned.png")
    success = clean_png_metadata(img_path, out_path)
    assert success is True
    assert os.path.exists(out_path)

    # 3. Проверяем, что метаданные отсутствуют
    with Image.open(out_path) as clean_img:
        assert "Software" not in clean_img.info
        assert "parameters" not in clean_img.info
        assert clean_img.size == (100, 100)


def test_clean_image_dispatch(temp_dir):
    # Тест на диспетчеризацию clean_image
    jpg_path = os.path.join(temp_dir, "test.jpg")
    img_jpg = Image.new("RGB", (50, 50), color="green")
    img_jpg.save(jpg_path, "JPEG")

    png_path = os.path.join(temp_dir, "test.png")
    img_png = Image.new("RGB", (50, 50), color="yellow")
    img_png.save(png_path, "PNG")

    out_jpg = os.path.join(temp_dir, "test_clean.jpg")
    out_png = os.path.join(temp_dir, "test_clean.png")

    assert clean_image(jpg_path, out_jpg) is True
    assert clean_image(png_path, out_png) is True
    assert os.path.exists(out_jpg)
    assert os.path.exists(out_png)

    # Невалидный файл должен возвращать False (graceful error handling)
    bad_path = os.path.join(temp_dir, "non_existent.jpg")
    assert clean_image(bad_path, os.path.join(temp_dir, "bad_out.jpg")) is False
