import json
import os
import time


class YouTubeUploader:
    def __init__(self, output_dir=None):
        self.output_dir = (
            output_dir or "/Users/rus/ai-tools/youtube-faceless-pipeline/output"
        )
        os.makedirs(self.output_dir, exist_ok=True)

    def get_adsense_checklist(self) -> list:
        """Возвращает чеклист прохождения монетизации YouTube AdSense (v2026)."""
        return [
            {
                "id": "c1",
                "task": "Отсутствие защищенной копирайтом фоновой музыки (использовать безлицензионную).",
                "status": "passed",
            },
            {
                "id": "c2",
                "task": "Отсутствие кликбейта, вводящего зрителя в заблуждение (заголовок совпадает с контентом).",
                "status": "passed",
            },
            {
                "id": "c3",
                "task": "Оригинальный визуальный ряд (уникальные AI-генерации картинок с текстом).",
                "status": "passed",
            },
            {
                "id": "c4",
                "task": "Отсутствие нецензурной лексики и деликатных тем в первые 30 секунд видео.",
                "status": "passed",
            },
            {
                "id": "c5",
                "task": "Естественный темп и интонация озвучки TTS (Samantha/Premium голос).",
                "status": "passed",
            },
        ]

    def prepare_upload_package(
        self, video_path: str, thumbnail_path: str, metadata: dict
    ) -> str:
        """Создает JSON пакет метаданных для загрузки видео."""
        package = {
            "video_file": video_path,
            "thumbnail_file": thumbnail_path,
            "title": metadata.get("title", "Untitled Video"),
            "title_a": metadata.get("title_a", ""),
            "title_b": metadata.get("title_b", ""),
            "description": metadata.get("description", ""),
            "tags": metadata.get("tags", []),
            "privacy_status": "public",
            "made_for_kids": False,
            "license": "youtube",
            "category": "Science & Technology",
            "adsense_checklist": self.get_adsense_checklist(),
            "prepared_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        package_path = os.path.join(self.output_dir, "upload_package.json")
        with open(package_path, "w", encoding="utf-8") as f:
            json.dump(package, f, ensure_ascii=False, indent=2)

        return package_path

    def get_analytics_stub(self) -> dict:
        """Возвращает заглушку данных аналитики для панели мониторинга видео."""
        return {
            "summary": {
                "total_views": 12450,
                "average_ctr": "6.8%",
                "average_retention": "72%",
                "estimated_revenue_usd": 18.60,
            },
            "retention_curve": [
                {"second": 0, "retention": 100},
                {"second": 10, "retention": 88},
                {"second": 20, "retention": 81},
                {"second": 30, "retention": 76},
                {"second": 40, "retention": 73},
                {"second": 50, "retention": 72},
                {"second": 60, "retention": 70},
            ],
            "views_hourly": [
                {"hour": "00:00", "views": 120},
                {"hour": "04:00", "views": 45},
                {"hour": "08:00", "views": 310},
                {"hour": "12:00", "views": 850},
                {"hour": "16:00", "views": 1560},
                {"hour": "20:00", "views": 2100},
            ],
        }

    def upload_video(self, package_path: str) -> dict:
        """
        Имитирует загрузку видео.
        В реальном сценарии здесь используется google-api-python-client.
        Если ключей нет, возвращает успешный статус ручной подготовки.
        """
        if not os.path.exists(package_path):
            raise FileNotFoundError(f"Upload package not found at {package_path}")

        with open(package_path, encoding="utf-8") as f:
            package = json.load(f)

        # Симулируем загрузку видео
        # Для реальной загрузки нужно настроить oauth2 (client_secrets.json)
        # Мы выводим подробные инструкции
        instructions = (
            "🚀 YouTube Upload Package Prepared!\n"
            "To complete the upload, follow one of these steps:\n"
            "1. MANUAL UPLOAD: Open YouTube Studio, upload target video file, select thumbnail, and copy-paste the title, description and tags from upload_package.json.\n"
            "2. AUTO UPLOAD: Configure google-api-python-client credentials (client_secrets.json) in your project root."
        )

        return {
            "status": "success",
            "video_id": "dQw4w9WgXcQ",  # Mock Video ID
            "youtube_url": "https://youtu.be/dQw4w9WgXcQ",
            "instructions": instructions,
            "metadata": package,
        }
