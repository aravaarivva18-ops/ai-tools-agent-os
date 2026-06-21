import os
import re
import subprocess  # nosec B404
import sys
import urllib.parse
import urllib.request

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

# Добавляем путь к родительской директории, чтобы импортировать seo_optimizer и upload_cli
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import seo_optimizer
import upload_cli


class ContentPolicyError(Exception):
    """Исключение, выбраемое при нарушении политики YouTube."""

    pass


class VideoGenerator:
    def __init__(self, output_dir=None):
        self.output_dir = (
            output_dir or "/Users/rus/ai-tools/youtube-faceless-pipeline/output"
        )
        os.makedirs(self.output_dir, exist_ok=True)
        self.ffmpeg_path = "/opt/homebrew/bin/ffmpeg"
        if not os.path.exists(self.ffmpeg_path):
            self.ffmpeg_path = "ffmpeg"  # Fallback to PATH

        # Черный список слов для проверки YouTube Policy Violations (насилие, спам, скам и т.д.)
        self.policy_blacklist = [
            r"violence",
            r"dangerous",
            r"scam",
            r"hack",
            r"kill",
            r"suicide",
            r"drugs",
            r"illegal",
            r"abuse",
            r"terror",
            r"weapon",
            r"fraud",
            r"насилие",
            r"взлом",
            r"мошенничество",
            r"опасный",
            r"убийство",
        ]

        # Инициализируем SEO оптимизатор
        self.seo = seo_optimizer.SEOOptimizer()

    def validate_content(self, text: str):
        """Проверяет контент на соответствие правилам безопасности YouTube."""
        for pattern in self.policy_blacklist:
            if re.search(pattern, text, re.IGNORECASE):
                raise ContentPolicyError(
                    f"YouTube Policy Violation: The content contains blacklisted pattern '{pattern}'."
                )

    def fetch_trends(self, niche: str) -> list:
        """
        Ищет тренды по нише с помощью agent-reach или last30days.
        В случае их отсутствия возвращает качественный список встроенных трендов.
        """
        self.validate_content(niche)
        niche_lower = niche.lower()
        if "autonomous" in niche_lower or "agents" in niche_lower:
            return [
                "autonomous AI agents running dev pipelines in 2026",
                "how AI agents solve complex business operations",
                "the rise of solo loop AI architectures",
                "multi-agent orchestration frameworks vs single loop",
            ]
        elif "tech" in niche_lower or "ai" in niche_lower:
            return [
                "autonomous AI agents running businesses",
                "generative video models for marketing",
                "local LLMs running on MacBook M5",
                "productivity loops with AI CLI tools",
            ]
        elif "productivity" in niche_lower:
            return [
                "time-blocking with glassmorphism calendars",
                "minimalist digital setups for deep work",
                "AI-assisted note-taking in Obsidian",
                "morning routine of a solo developer",
            ]
        else:
            return [
                f"hottest trends in {niche}",
                f"creative ideas about {niche}",
                f"what experts say about {niche}",
            ]

    def generate_script(self, niche: str, trends: list) -> dict:
        """
        Генерирует сценарий для видео (заголовок, описание, теги и сцены).
        В реальном приложении здесь вызывается LLM, в MVP возвращается структурированный шаблон на основе трендов.
        """
        self.validate_content(niche)
        for trend in trends:
            self.validate_content(trend)

        trend1 = trends[0] if len(trends) > 0 else "AI Automation"
        trend2 = trends[1] if len(trends) > 1 else "Future Tech"

        niche_lower = niche.lower()
        if "autonomous" in niche_lower or "agents" in niche_lower:
            scenes = [
                {
                    "text": "Привет! В две тысячи двадцать шестом году автономные ИИ-агенты вышли на совершенно новый уровень и теперь они способны управлять реальными коммерческими проектами и бизнесами полностью самостоятельно без какого-либо вмешательства со стороны человека.",
                    "visual_prompt": "Futuristic clean laboratory with glowing neon cyan lines, professional dashboard displayed on screen, hyperrealistic, dark mood",
                },
                {
                    "text": "В основе всей этой невероятной системы лежит передовая архитектура Solo Loop. ИИ-агент самостоятельно ставит себе задачи, пишет программный код, разворачивает облачные серверы, настраивает базы данных и проводит полную SEO-оптимизацию.",
                    "visual_prompt": "Abstract cybernetic brain connection nodes, digital neural network interface, glowing blue particles, cinematic lighting",
                },
                {
                    "text": "Автономные онлайн-магазины, интеллектуальные рекламные кампании в соцсетях и автоматический юридический аудит сложных контрактов — все эти рутинные процессы теперь выполняются роботами со скоростью, превышающей человеческую в десятки раз.",
                    "visual_prompt": "Digital data stream matrix, golden particle effects flowing through dark virtual corridor, high technology background",
                },
                {
                    "text": "Новейшие технологические решения, такие как революционная платформа ChipStack AI, наглядно продемонстрировали на выставке Computex 2026, что виртуальные инженеры могут проектировать сложнейшие микропроцессоры за считанные минуты.",
                    "visual_prompt": "Detailed silicon microchip layout glowing green, virtual schematic blueprint overlay, high tech render",
                },
                {
                    "text": "В этой новой реальности человек смещается в роль высокоуровневого рецензента и контролера по знаменитому правилу Dan Martell 10-80-10, экономя колоссальное количество своего драгоценного времени и ментальной энергии.",
                    "visual_prompt": "Minimalist digital productivity space, smooth neon purple highlights, elegant dashboard showing time saved",
                },
                {
                    "text": "Если вы хотите узнать, как запустить и масштабировать свой собственный полностью автоматизированный ИИ-бизнес, обязательно подписывайтесь на наш канал. Мы покажем вам весь процесс разработки от А до Я!",
                    "visual_prompt": "Futuristic neon red subscribe button hovering in dynamic abstract cyberspace backdrop, cinematic render",
                },
            ]
        else:
            scenes = [
                {
                    "text": f"Here is the truth about {trend1} in 2026. It is changing faster than ever.",
                    "visual_prompt": "futuristic laboratory with glowing neon lines, high tech computer screen displaying charts, hyperrealistic, dark mood, purple neon accents",
                },
                {
                    "text": f"This is why {trend2} will change everything in our daily productivity loop.",
                    "visual_prompt": "abstract cybernetic brain connection nodes, digital neural network interface, glowing blue and cyan particles, cinematic lighting",
                },
                {
                    "text": "The era of manual work is coming to an end. Join the automation era today.",
                    "visual_prompt": "minimalist neon red subscribe button hovering in a futuristic abstract cyberspace background, cinematic render",
                },
            ]

        script = {
            "title": f"The Future of {niche.split('/')[-1].capitalize()}: {trend1.title()}",
            "description": f"How {trend1} and {trend2} are reshaping the world. Stay tuned for details! #technology #faceless #ai",
            "tags": [niche.split("/")[-1], "tech", "faceless", "ai", "trends"],
            "scenes": scenes,
        }

        # Валидация сгенерированного сценария
        for scene in script["scenes"]:
            self.validate_content(scene["text"])
            self.validate_content(scene["visual_prompt"])

        return script

    def generate_image(self, prompt: str, path: str):
        """
        Генерирует изображение. Сначала пробует скачать из бесплатного Pollinations AI.
        В случае сбоя или отсутствия сети рисует красивый градиентный плейсхолдер с помощью Pillow.
        """
        self.validate_content(prompt)
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1080&height=1920&nologo=true"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as response:  # nosec B310
                with open(path, "wb") as f:
                    f.write(response.read())
            return
        except Exception:
            self._create_fallback_image(prompt, path)

    def _create_fallback_image(self, prompt: str, path: str):
        """Создает стильный вертикальный градиент с текстом промпта с помощью Pillow."""
        width, height = 1080, 1920
        image = PIL.Image.new("RGB", (width, height), "#0b0d19")
        draw = PIL.ImageDraw.Draw(image)

        # Рисуем красивый градиент
        for y in range(height):
            r = int(11 + (15 - 11) * (y / height))
            g = int(13 + (40 - 13) * (y / height))
            b = int(25 + (90 - 25) * (y / height))
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Рисуем декоративные неоновые круги (glow эффект)
        draw.ellipse((-200, 300, 600, 1100), outline="#8b5cf6", width=2)
        draw.ellipse((600, 1000, 1300, 1700), outline="#06b6d4", width=2)

        # Текст (промпт) по центру
        text_to_draw = f"PROMPT:\n{prompt}"
        words = text_to_draw.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 30:
                lines.append(" ".join(current_line))
                current_line = []
        if current_line:
            lines.append(" ".join(current_line))
        text_lines = "\n".join(lines)

        font = None
        for font_path in [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]:
            if os.path.exists(font_path):
                try:
                    font = PIL.ImageFont.truetype(font_path, 40)
                    break
                except Exception:  # nosec B110
                    pass

        if font is None:
            font = PIL.ImageFont.load_default()

        # Рисуем подложку
        draw.rectangle([100, 800, 980, 1200], fill=(0, 0, 0, 180))
        draw.text((120, 820), text_lines, fill="#f3f4f6", font=font)
        image.save(path, "JPEG")

    def generate_speech(self, text: str, path: str):
        """
        Генерирует озвучку текста. На macOS использует команду say.
        В случае сбоя делает fallback на генерацию тишины через FFmpeg.
        """
        self.validate_content(text)
        try:
            temp_aac = path + ".aac"
            cmd = ["say", "-o", temp_aac, text]
            subprocess.run(cmd, check=True)  # nosec B603

            conv_cmd = [
                self.ffmpeg_path,
                "-y",
                "-i",
                temp_aac,
                "-acodec",
                "pcm_s16le",
                "-ar",
                "22050",
                path,
            ]
            subprocess.run(
                conv_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )  # nosec B603

            if os.path.exists(temp_aac):
                os.remove(temp_aac)
            return
        except Exception:
            self._create_fallback_speech(text, path)

    def _create_fallback_speech(self, text: str, path: str):
        """Создает тихий аудиофайл длины, пропорциональной количеству слов (0.5 сек на слово)."""
        word_count = len(text.split())
        duration = max(2, int(word_count * 0.5))  #  Минимум 2 секунды

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=22050:cl=mono",
            "-t",
            str(duration),
            path,
        ]
        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )  # nosec B603

    def _get_audio_duration(self, audio_path: str) -> float:
        """Определяет длительность аудиофайла."""
        try:
            ffprobe_cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ]
            res = subprocess.run(
                ffprobe_cmd, capture_output=True, text=True, check=True
            )  # nosec B603
            return float(res.stdout.strip())
        except Exception:
            if os.path.exists(audio_path):
                size = os.path.getsize(audio_path)
                data_size = size - 44
                duration = data_size / (22050 * 2)
                return max(2.0, duration)
            return 3.0

    def _wrap_text(self, text: str, max_chars=25) -> str:
        """Разбивает длинный текст на строки."""
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > max_chars:
                lines.append(" ".join(current_line))
                current_line = []
        if current_line:
            lines.append(" ".join(current_line))
        return "\n".join(lines)

    def _add_text_to_image(self, image_path: str, text: str):
        """Накладывает стильный текст субтитров на изображение."""
        if not os.path.exists(image_path):
            return

        try:
            image = PIL.Image.open(image_path)
            draw = PIL.ImageDraw.Draw(image, "RGBA")
            width, height = image.size

            wrapped_text = self._wrap_text(text, max_chars=25)
            text_lines = wrapped_text.split("\n")

            font = None
            for font_path in [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]:
                if os.path.exists(font_path):
                    try:
                        font = PIL.ImageFont.truetype(font_path, 46)
                        break
                    except Exception:  # nosec B110
                        pass

            if font is None:
                font = PIL.ImageFont.load_default()

            try:
                max_w = 0
                total_h = 0
                line_spacing = 15
                for line in text_lines:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    w = bbox[2] - bbox[0]
                    h = bbox[3] - bbox[1]
                    if w > max_w:
                        max_w = w
                    total_h += h + line_spacing
                total_h -= line_spacing
            except AttributeError:
                max_w = 800
                total_h = len(text_lines) * 60

            center_x = width // 2
            center_y = int(height * 0.75)

            pad_x = 40
            pad_y = 30
            rect_x0 = max(20, center_x - max_w // 2 - pad_x)
            rect_x1 = min(width - 20, center_x + max_w // 2 + pad_x)
            rect_y0 = center_y - total_h // 2 - pad_y
            rect_y1 = center_y + total_h // 2 + pad_y

            try:
                draw.rounded_rectangle(
                    [rect_x0, rect_y0, rect_x1, rect_y1], radius=15, fill=(0, 0, 0, 180)
                )
            except AttributeError:
                draw.rectangle(
                    [rect_x0, rect_y0, rect_x1, rect_y1], fill=(0, 0, 0, 180)
                )

            curr_y = rect_y0 + pad_y
            for line in text_lines:
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    w = bbox[2] - bbox[0]
                    h = bbox[3] - bbox[1]
                except AttributeError:
                    w = len(line) * 20
                    h = 40

                x_pos = center_x - w // 2
                draw.text((x_pos, curr_y), line, fill="#ffffff", font=font)
                curr_y += h + 15

            image.save(image_path, "JPEG")
        except Exception:  # nosec B110
            pass

    def assemble_scene_video(
        self, image_path: str, audio_path: str, text: str, output_path: str
    ):
        """Сшивает картинку и аудио в один mp4 файл."""
        duration = self._get_audio_duration(audio_path)
        self._add_text_to_image(image_path, text)

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-loop",
            "1",
            "-i",
            image_path,
            "-i",
            audio_path,
            "-c:v",
            "libx264",
            "-t",
            f"{duration:.2f}",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            output_path,
        ]

        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )  # nosec B603

    def run_pipeline(self, niche: str) -> tuple[str, dict]:
        """Запускает полный пайплайн."""
        self.validate_content(niche)

        # 1. Research
        trends = self.fetch_trends(niche)

        # 2. Script
        script = self.generate_script(niche, trends)

        # 3. Similarity check
        full_text = " ".join([scene["text"] for scene in script["scenes"]])
        similarity = self.seo.check_similarity(full_text)

        # Уникальность должна быть > 60%, то есть сходство по Жаккару < 40% (0.40)
        if similarity > 0.40:
            raise ContentPolicyError(
                f"Duplicate content warning: script has {similarity * 100:.1f}% similarity with past videos (max allowed: 40.0%)."
            )

        self.seo.save_to_database(full_text)

        # 4. SEO Optimization
        optimized_metadata = self.seo.optimize_metadata(script)
        script.update(optimized_metadata)

        # 5. Thumbnail Generation
        thumbnail_prompt = self.seo.generate_thumbnail_prompt(
            optimized_metadata["title"]
        )
        thumbnail_path = os.path.join(self.output_dir, "thumbnail.jpg")
        self.generate_image(thumbnail_prompt, thumbnail_path)

        # 6. Assets Generation & Assembly
        temp_scenes = []
        for i, scene in enumerate(script["scenes"]):
            img_path = os.path.join(self.output_dir, f"image_{i}.jpg")
            aud_path = os.path.join(self.output_dir, f"audio_{i}.wav")
            scene_mp4 = os.path.join(self.output_dir, f"scene_{i}.mp4")

            self.generate_image(scene["visual_prompt"], img_path)
            self.generate_speech(scene["text"], aud_path)
            self.assemble_scene_video(img_path, aud_path, scene["text"], scene_mp4)
            temp_scenes.append(scene_mp4)

        # 7. Concat Scenes
        concat_txt_path = os.path.join(self.output_dir, "concat.txt")
        with open(concat_txt_path, "w") as f:
            for scene_path in temp_scenes:
                f.write(f"file '{os.path.basename(scene_path)}'\n")

        final_video_path = os.path.join(self.output_dir, "final_video.mp4")

        concat_cmd = [
            self.ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_txt_path,
            "-c",
            "copy",
            final_video_path,
        ]
        subprocess.run(
            concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )  # nosec B603

        for p in temp_scenes:
            if os.path.exists(p):
                os.remove(p)
        if os.path.exists(concat_txt_path):
            os.remove(concat_txt_path)

        # 8. Создаем пакет загрузки
        uploader = upload_cli.YouTubeUploader(output_dir=self.output_dir)
        package_path = uploader.prepare_upload_package(
            final_video_path, thumbnail_path, optimized_metadata
        )

        script["thumbnail_path"] = thumbnail_path
        script["upload_package_path"] = package_path
        script["adsense_checklist"] = uploader.get_adsense_checklist()
        script["analytics"] = uploader.get_analytics_stub()

        return final_video_path, script
