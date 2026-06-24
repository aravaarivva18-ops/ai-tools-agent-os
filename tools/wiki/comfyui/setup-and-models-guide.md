# 🚀 Руководство по развертыванию ComfyUI на Vast.ai и модели

Это руководство содержит пошаговую инструкцию по установке ComfyUI, всех необходимых кастомных нод и скачиванию весов моделей на облачной GPU-платформе **Vast.ai**, а также рекомендации по выбору моделей для обеспечения максимальной фотореалистичности и консистентности лица.

---

## ☁️ Часть 1. Развертывание на Vast.ai (Пошаговый гайд)

**Vast.ai** предоставляет дешевую аренду GPU. Для комфортной работы с фото-апскейлерами (SUPIR) и генерацией видео (AnimateDiff) рекомендуется выбирать инстансы с видеопамятью **VRAM ≥24 ГБ** (RTX 3090, RTX 4090, RTX A6000, A40).

### Шаг 1. Выбор шаблона и аренда
1. Зарегистрируйтесь на [Vast.ai](https://vast.ai/) и пополните баланс.
2. Перейдите в раздел **Templates** и выберите официальный шаблон **PyTorch** (например, `pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime` или более новый с CUDA 12).
3. В настройках шаблона (Edit Selected Template):
   * Убедитесь, что включен **Jupyter-сервер** (для удобного скачивания файлов).
   * Откройте порты: добавьте порт `8188` (порт ComfyUI по умолчанию) во вкладку внешних портов или используйте прокси-опцию Vast.ai.
4. Перейдите во вкладку **Search**, выберите подходящую видеокарту (например, RTX 4090) и нажмите **Rent**.

### Шаг 2. Подключение к серверу
После того как инстанс перейдет в статус `Running`, подключитесь к нему через SSH из вашего терминала:
```bash
ssh -p <PORT> root@<IP_ADDRESS> -L 8188:127.0.0.1:8188
```
> [!TIP]
> Флаг `-L 8188:127.0.0.1:8188` настраивает **SSH-туннелирование**. После этого вы сможете открыть ComfyUI в своем локальном браузере по адресу `http://127.0.0.1:8188`, даже если на сервере закрыты внешние порты.

---

### Шаг 3. Запуск скрипта автоматической установки
Выполните следующие команды в терминале Vast.ai (в папке `/workspace` для сохранения данных при перезагрузках):

```bash
# Переходим в рабочую директорию, которая сохраняется на Vast.ai
cd /workspace

# Обновляем пакетный менеджер и ставим утилиты
apt-get update && apt-get install -y git wget curl ffmpeg libgl1-mesa-glx libglib2.0-0

# Клонируем официальный ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# Создаем виртуальное окружение Python
python3 -m venv venv
source venv/bin/activate

# Обновляем pip и ставим PyTorch с поддержкой CUDA
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Устанавливаем базовые зависимости ComfyUI
pip install -r requirements.txt

# Устанавливаем comfy-cli для удобного менеджмента нод
pip install comfy-cli
comfy --install-completion
```

---

### Шаг 4. Установка кастомных нод (Custom Nodes)
Установим все необходимые ноды для работы фото- и видео-воркфлоу:

```bash
# Переходим в папку кастомных нод
cd /workspace/ComfyUI/custom_nodes

# 1. ComfyUI Manager
git clone https://github.com/ltdrdata/ComfyUI-Manager.git

# 2. Impact Pack (для детекторов лица и Face Detailer)
git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git

# 3. IP-Adapter Plus (для консистентности лица)
git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git

# 4. InstantID (для жесткого переноса структуры лица)
git clone https://github.com/ZHO-ZHO-ZHO/ComfyUI-InstantID.git

# 5. Advanced ControlNet
git clone https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet.git

# 6. AnimateDiff Evolved (для видео-генерации)
git clone https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git

# 7. Florence-2 (для авто-промптинга)
git clone https://github.com/kijai/ComfyUI-Florence2.git

# 8. LivePortrait (для мимики лица на видео)
git clone https://github.com/kijai/ComfyUI-LivePortraitKJ.git

# 9. Frame Interpolation (для FILM плавности видео)
git clone https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git

# Устанавливаем зависимости для установленных нод
cd /workspace/ComfyUI
comfy node install-deps
```

---

## 📦 Часть 2. Быстрая загрузка моделей (модели для Vast.ai)

Скачивать модели на Vast.ai нужно напрямую по URL через `wget` в фоновом режиме, чтобы использовать максимальную скорость облачного интернет-канала (обычно 1–10 Гбит/с).

### 1. Чекпоинты (Базовые модели)
Мы используем **SDXL** (Juggernaut XL) для фото-воркфлоу и **SD 1.5** (DreamShaper 8) для видео-воркфлоу (из-за совместимости с AnimateDiff):

```bash
# Juggernaut XL v9 (SDXL - для фото)
wget -O /workspace/ComfyUI/models/checkpoints/juggernautXL_v9RdPhoto2Lightning.safetensors \
"https://civitai.com/api/download/models/357609?type=Model&format=SafeTensor&size=pruned&fp=fp16"

# DreamShaper 8 (SD 1.5 - для видео)
wget -O /workspace/ComfyUI/models/checkpoints/dreamshaper_8.safetensors \
"https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors"
```

### 2. Модели InstantID & IP-Adapter (Лицо)
```bash
# Создаем папки
mkdir -p /workspace/ComfyUI/models/instantid
mkdir -p /workspace/ComfyUI/models/ipadapter
mkdir -p /workspace/ComfyUI/models/clip_vision

# CLIP Vision (необходима для работы IP-Adapter FaceID)
wget -O /workspace/ComfyUI/models/clip_vision/clip_vision_g.safetensors \
"https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors"

# InstantID ControlNet (SDXL)
wget -O /workspace/ComfyUI/models/controlnet/control_instant_id_sdxl.safetensors \
"https://huggingface.co/InstantX/InstantID/resolve/main/ControlNetModel/diffusion_pytorch_model.safetensors"

# InstantID InsightFace (лицо)
wget -O /workspace/ComfyUI/models/instantid/ip-adapter.bin \
"https://huggingface.co/InstantX/InstantID/resolve/main/ip-adapter.bin"

# IP-Adapter FaceID Plus v2 SDXL (для фото)
wget -O /workspace/ComfyUI/models/ipadapter/ip-adapter-faceid-plusv2_sdxl.bin \
"https://huggingface.co/h94/IP-Adapter-FaceID/resolve/main/ip-adapter-faceid-plusv2_sdxl.bin"

# Lora для FaceID Plus v2 SDXL
wget -O /workspace/ComfyUI/models/loras/ip-adapter-faceid-plusv2_sdxl_lora.safetensors \
"https://huggingface.co/h94/IP-Adapter-FaceID/resolve/main/ip-adapter-faceid-plusv2_sdxl_lora.safetensors"

# IP-Adapter FaceID Plus v2 SD1.5 (для видео)
wget -O /workspace/ComfyUI/models/ipadapter/ip-adapter-faceid-plusv2_sd15.bin \
"https://huggingface.co/h94/IP-Adapter-FaceID/resolve/main/ip-adapter-faceid-plusv2_sd15.bin"
```

### 3. Модели ControlNet (SDXL & SD1.5)
```bash
# OpenPose (SDXL - для фото)
wget -O /workspace/ComfyUI/models/controlnet/controlnet-openpose-sdxl.safetensors \
"https://huggingface.co/thibaud/controlnet-openpose-sdxl-1.0/resolve/main/OpenPoseXL2.safetensors"

# Depth (SDXL - для фото, опционально)
wget -O /workspace/ComfyUI/models/controlnet/controlnet-depth-sdxl.safetensors \
"https://huggingface.co/diffusers/controlnet-depth-sdxl-1.0/resolve/main/diffusion_pytorch_model.safetensors"

# OpenPose (SD 1.5 - для видео)
wget -O /workspace/ComfyUI/models/controlnet/control_v11p_sd15_openpose.safetensors \
"https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose.safetensors"

# Tile (SD 1.5 - для временной стабильности видео)
wget -O /workspace/ComfyUI/models/controlnet/control_v11f1e_sd15_tile.safetensors \
"https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11f1e_sd15_tile.safetensors"
```

### 4. Моушн-модели AnimateDiff (Видео)
```bash
mkdir -p /workspace/ComfyUI/custom_nodes/ComfyUI-AnimateDiff-Evolved/models

# Motion Module SD1.5 v3 (LCM для быстрого рендера)
wget -O /workspace/ComfyUI/custom_nodes/ComfyUI-AnimateDiff-Evolved/models/v3_sd15_mm.ckpt \
"https://huggingface.co/guoyww/AnimateDiff/resolve/main/v3_sd15_mm.ckpt"
```

### 5. Модели Апскейла и Детекции лиц (Upscale & Face Detection)
```bash
# Создаем папки
mkdir -p /workspace/ComfyUI/models/upscale_models
mkdir -p /workspace/ComfyUI/models/ultralytics/bbox

# 4x-UltraSharp (модель апскейлера)
wget -O /workspace/ComfyUI/models/upscale_models/4x-UltraSharp.pth \
"https://huggingface.co/lokCX/4x-Ultrasharp/resolve/main/4x-UltraSharp.pth"

# Yolov8 Face Detector (детектор лиц для FaceDetailer)
wget -O /workspace/ComfyUI/models/ultralytics/bbox/face_yolov8m.pt \
"https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8m.pt"
```

---

## 🚀 Часть 3. Запуск и подключение

После установки всего окружения и загрузки моделей запустите сервер:

```bash
cd /workspace/ComfyUI
source venv/bin/activate

# Запуск с прослушиванием всех интерфейсов (важно для облаков)
python3 main.py --listen 0.0.0.0 --port 8188
```

Откройте ваш локальный браузер по адресу `http://127.0.0.1:8188` (при запущенном SSH-туннеле) или используйте HTTPS-ссылку, предоставляемую Vast.ai во вкладке **Instances -> GUI / Open Port**.
