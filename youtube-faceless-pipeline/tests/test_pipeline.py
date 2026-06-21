import os
import shutil
import sys
import unittest.mock

import pytest

# Добавляем путь к локальной папке tools в sys.path для избежания коллизий
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"),
)
import content_gen

# Создаем временную директорию для вывода тестов
TEST_OUTPUT_DIR = "/Users/rus/ai-tools/youtube-faceless-pipeline/tests/output"


@pytest.fixture(autouse=True)
def setup_test_env():
    """Создает и очищает временную директорию перед каждым тестом."""
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

    # Очищаем базу данных дубликатов для изоляции тестов
    db_path = os.path.join(TEST_OUTPUT_DIR, "generated_scripts_db.json")
    if os.path.exists(db_path):
        os.remove(db_path)

    yield

    # Очищаем после тестов
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)


def test_pipeline_positive_cycle():
    """
    Положительный тест: Проверяет полный цикл генерации видео,
    включая SEO, Thumbnail, лимиты уникальности контента и AdSense чеклист.
    """
    generator = content_gen.VideoGenerator(output_dir=TEST_OUTPUT_DIR)
    # Настраиваем путь к тестовой БД
    generator.seo.database_path = os.path.join(
        TEST_OUTPUT_DIR, "generated_scripts_db.json"
    )

    mock_script = {
        "title": "5 Mind-Blowing AI Trends in 2026",
        "description": "Discover the latest AI trends.",
        "tags": ["ai", "trends"],
        "scenes": [
            {
                "text": "Artificial Intelligence is evolving faster than ever.",
                "visual_prompt": "futuristic computer",
            },
            {
                "text": "Autonomous agents are running complex pipelines.",
                "visual_prompt": "holographic robots",
            },
        ],
    }

    with unittest.mock.patch.object(
        generator, "fetch_trends", return_value=["autonomous agents", "AGI 2026"]
    ):
        with unittest.mock.patch.object(
            generator, "generate_script", return_value=mock_script
        ):
            with unittest.mock.patch.object(
                generator,
                "generate_image",
                side_effect=lambda prompt, path: generator._create_fallback_image(
                    prompt, path
                ),
            ):
                with unittest.mock.patch.object(
                    generator,
                    "generate_speech",
                    side_effect=lambda text, path: generator._create_fallback_speech(
                        text, path
                    ),
                ):
                    video_path, metadata = generator.run_pipeline(
                        niche="tech/AI/productivity"
                    )

                    assert os.path.exists(video_path), "Файл видео не был создан"
                    assert "thumbnail_path" in metadata
                    assert "upload_package_path" in metadata
                    assert "adsense_checklist" in metadata
                    assert "analytics" in metadata
                    assert os.path.exists(metadata["thumbnail_path"]), (
                        "Thumbnail не был создан"
                    )
                    assert os.path.exists(metadata["upload_package_path"]), (
                        "Upload package не был создан"
                    )


def test_pipeline_negative_invalid_niche():
    """Отрицательный тест: Проверяет вызов ошибки при запрещенной нише."""
    generator = content_gen.VideoGenerator(output_dir=TEST_OUTPUT_DIR)
    invalid_niche = "violence/dangerous hacks/scams"

    with pytest.raises(content_gen.ContentPolicyError) as exc_info:
        generator.run_pipeline(niche=invalid_niche)

    assert "YouTube Policy Violation" in str(exc_info.value)


def test_pipeline_duplicate_content_check():
    """
    Отрицательный тест: Проверяет работу similarity check.
    Если новый сценарий полностью дублирует ранее созданный, должна выбрасываться ошибка политики уникальности.
    """
    generator = content_gen.VideoGenerator(output_dir=TEST_OUTPUT_DIR)
    generator.seo.database_path = os.path.join(
        TEST_OUTPUT_DIR, "generated_scripts_db.json"
    )

    mock_script = {
        "title": "5 Mind-Blowing AI Trends in 2026",
        "description": "Discover the latest AI trends.",
        "tags": ["ai", "trends"],
        "scenes": [
            {
                "text": "Artificial Intelligence is evolving faster than ever.",
                "visual_prompt": "futuristic computer",
            },
            {
                "text": "Autonomous agents are running complex pipelines.",
                "visual_prompt": "holographic robots",
            },
        ],
    }

    with unittest.mock.patch.object(
        generator, "fetch_trends", return_value=["autonomous agents", "AGI 2026"]
    ):
        with unittest.mock.patch.object(
            generator, "generate_script", return_value=mock_script
        ):
            with unittest.mock.patch.object(
                generator,
                "generate_image",
                side_effect=lambda prompt, path: generator._create_fallback_image(
                    prompt, path
                ),
            ):
                with unittest.mock.patch.object(
                    generator,
                    "generate_speech",
                    side_effect=lambda text, path: generator._create_fallback_speech(
                        text, path
                    ),
                ):
                    # Первый прогон (успешный)
                    generator.run_pipeline(niche="tech/AI/productivity")

                    # Второй прогон с тем же контентом (должен вызвать ошибку дублирования)
                    with pytest.raises(content_gen.ContentPolicyError) as exc_info:
                        generator.run_pipeline(niche="tech/AI/productivity")

                    assert "Duplicate content warning" in str(exc_info.value)
