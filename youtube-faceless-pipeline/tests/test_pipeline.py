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
    Также проверяет наличие A/B заголовков и длительность видео > 90 секунд.
    """
    import json

    generator = content_gen.VideoGenerator(output_dir=TEST_OUTPUT_DIR)
    # Настраиваем путь к тестовой БД
    generator.seo.database_path = os.path.join(
        TEST_OUTPUT_DIR, "generated_scripts_db.json"
    )

    # Создаем 7 длинных сцен, чтобы суммарная длительность превысила 90 секунд.
    # В _create_fallback_speech длительность сцены: max(2, int(word_count * 0.5))
    mock_script = {
        "title": "5 Mind-Blowing AI Trends: Автономные ИИ Агенты 2026",
        "description": "Discover the latest AI trends.",
        "tags": ["ai", "trends"],
        "scenes": [
            {
                "text": "Привет! В две тысячи двадцать шестом году автономные ИИ-агенты вышли на совершенно новый уровень и теперь они способны управлять реальными коммерческими проектами и бизнесами полностью самостоятельно без какого-либо вмешательства со стороны человека.",
                "visual_prompt": "Futuristic clean laboratory with glowing neon cyan lines",
            },
            {
                "text": "В основе всей этой невероятной системы лежит передовая архитектура Solo Loop. ИИ-агент самостоятельно ставит себе задачи, пишет программный код, разворачивает облачные серверы, настраивает базы данных и проводит полную SEO-оптимизацию.",
                "visual_prompt": "Abstract cybernetic brain connection nodes",
            },
            {
                "text": "Автономные онлайн-магазины, интеллектуальные рекламные кампании в соцсетях и автоматический юридический аудит сложных контрактов — все эти рутинные процессы теперь выполняются роботами со скоростью, превышающей человеческую в десятки раз.",
                "visual_prompt": "Digital data stream matrix",
            },
            {
                "text": "Новейшие технологические решения, такие как революционная платформа ChipStack AI, наглядно продемонстрировали на выставке Computex 2026, что виртуальные инженеры могут проектировать сложнейшие микропроцессоры за считанные минуты.",
                "visual_prompt": "Detailed silicon microchip layout glowing green",
            },
            {
                "text": "В этой новой реальности человек смещается в роль высокоуровневого рецензента и контролера по знаменитому правилу Dan Martell 10-80-10, экономя колоссальное количество своего драгоценного времени и ментальной энергии.",
                "visual_prompt": "Minimalist digital productivity space",
            },
            {
                "text": "Если вы хотите узнать, как запустить и масштабировать свой собственный полностью автоматизированный ИИ-бизнес, обязательно подписывайтесь на наш канал. Мы покажем вам весь процесс разработки от А до Я!",
                "visual_prompt": "Futuristic neon red subscribe button hovering in dynamic abstract cyberspace backdrop",
            },
            {
                "text": "Мы регулярно публикуем самые актуальные обзоры передовых технологий, практические руководства по интеграции нейронных сетей и эксклюзивные интервью с ведущими мировыми экспертами в области искусственного интеллекта и робототехники.",
                "visual_prompt": "Futuristic conference hall with dynamic digital projections",
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

                    # Проверка A/B заголовков в метаданных и в пакете загрузки
                    assert "title_a" in metadata, (
                        "Вариант A заголовка отсутствует в метаданных"
                    )
                    assert "title_b" in metadata, (
                        "Вариант B заголовка отсутствует в метаданных"
                    )

                    with open(metadata["upload_package_path"], encoding="utf-8") as f:
                        package_data = json.load(f)
                    assert package_data.get("title_a") == metadata["title_a"], (
                        "Неверный title_a в пакете загрузки"
                    )
                    assert package_data.get("title_b") == metadata["title_b"], (
                        "Неверный title_b в пакете загрузки"
                    )

                    # Проверка длительности сгенерированного видео
                    duration = generator._get_audio_duration(video_path)
                    assert duration > 90.0, (
                        f"Длительность видео {duration} с должна быть больше 90 с"
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
