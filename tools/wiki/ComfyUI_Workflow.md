# ComfyUI Workflow для консистентного персонажа

База знаний по созданию автоматизированного workflow в ComfyUI для генерации фото и видео с единым персонажем для Kwork-заказов.

## 🏗️ Архитектура Workflow

Пайплайн делится на 5 ключевых зон:
1. **Inputs Panel**: Панель ввода текстовых описаний, настроек света, ракурсов и эмоций.
2. **LLM Prompt Gen**: Нода-генератор (через Groq API или Ollama) для превращения краткого описания в промпт профессионального качества.
3. **LoRA + Face-Lock (InstantID)**: Гибридная посадка лица ( LoRA лица + InstantID / IP-Adapter FaceID) для 98-100% консистентности персонажа без искажений при смене ракурса.
4. **KSampler + Upscale (FaceDetailer)**: Генерация на базе SDXL/Flux с финализацией лица через FaceDetailer и общим апскейлом.
5. **Video Engine (LivePortrait)**: Мгновенный перенос мимики с управляющего видео (селфи) на полученную фотографию без "плавания" лица.

## 🛠️ Перечень кастомных нод для установки
* `ComfyUI-Manager`
* `ComfyUI-Impact-Pack`
* `ComfyUI-IP-Adapter-Plus`
* `ComfyUI_InstantID`
* `ComfyUI-LivePortrait`
* `ComfyUI-ControlNet-Aux`
* `ComfyUI-VideoHelperSuite`

## 💻 Специфика запуска на Apple Silicon (MacBook Air M5 16GB)
* Использование моделей SDXL с FP16/FP8 точностью.
* Применение **LivePortrait** для видео вместо Hunyuan/AnimateDiff — это снижает нагрузку на RAM и генерирует анимацию за секунды.
* Принудительное ограничение размера текстур при апскейле до 1.5x-2x.
