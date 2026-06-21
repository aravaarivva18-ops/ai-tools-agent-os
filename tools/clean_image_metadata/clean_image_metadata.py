#!/usr/bin/env python3
"""
Image Metadata Cleaner
Utility for removing EXIF and XMP metadata from JPEG and PNG images.
Provides both a CLI and a beautiful Tkinter GUI.
"""

import os
import shutil
import sys

import piexif
from PIL import Image

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    HAS_TKINTER = True
    ParentCanvas = tk.Canvas
except ImportError:
    HAS_TKINTER = False
    ParentCanvas = object

    class DummyTk:
        def __getattr__(self, name):
            return object

    tk = DummyTk()

# Попытка импортировать библиотеку для drag-and-drop в Tkinter
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    HAS_DND = True
except ImportError:
    HAS_DND = False


def clean_jpeg_metadata(input_path: str, output_path: str) -> bool:
    """
    Удаляет EXIF-метаданные из JPEG-изображения.
    Сначала копирует файл, затем применяет piexif.remove для сохранения качества.
    В случае сбоя piexif использует пересохранение через Pillow.
    """
    try:
        if not os.path.exists(input_path):
            return False

        # Сначала копируем исходный файл в целевой путь
        shutil.copy2(input_path, output_path)

        try:
            # Пытаемся удалить метаданные без пересжатия (lossless для изображения)
            piexif.remove(output_path)
            return True
        except Exception:
            # Резервный метод: пересохранение через Pillow без метаданных
            with Image.open(input_path) as img:
                img.save(output_path, "JPEG", exif=b"")
            return True
    except Exception as e:
        print(f"Ошибка при очистке JPEG {input_path}: {e}", file=sys.stderr)
        return False


def clean_png_metadata(input_path: str, output_path: str) -> bool:
    """
    Удаляет текстовые метаданные (tEXt, zTXt, iTXt чанки) из PNG-изображения.
    """
    try:
        if not os.path.exists(input_path):
            return False

        with Image.open(input_path) as img:
            # Pillow при сохранении по умолчанию не пишет оригинальные метаданные (pnginfo),
            # если мы их явно не передаем.
            # Мы сохраняем изображение, сохраняя его оригинальный формат и палитру.
            img.save(output_path, "PNG")
        return True
    except Exception as e:
        print(f"Ошибка при очистке PNG {input_path}: {e}", file=sys.stderr)
        return False


def clean_image(input_path: str, output_path: str) -> bool:
    """
    Определяет формат изображения по расширению и вызывает соответствующую очистку.
    """
    try:
        if not os.path.exists(input_path):
            return False

        ext = os.path.splitext(input_path.lower())[1]
        if ext in (".jpg", ".jpeg"):
            return clean_jpeg_metadata(input_path, output_path)
        elif ext == ".png":
            return clean_png_metadata(input_path, output_path)
        else:
            # Для других форматов пробуем просто пересохранить через Pillow без exif/info
            with Image.open(input_path) as img:
                img.save(output_path)
            return True
    except Exception as e:
        print(f"Ошибка при обработке {input_path}: {e}", file=sys.stderr)
        return False


# --- Градиентный прогресс-бар для Tkinter ---
class GradientProgressBar(ParentCanvas):
    def __init__(
        self,
        parent,
        width=500,
        height=15,
        bg_color="#1E293B",
        start_color="#8B5CF6",
        end_color="#06B6D4",
        **kwargs,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=bg_color,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self.width = width
        self.height = height
        self.bg_color = bg_color

        # Парсинг RGB для интерполяции
        self.r1, self.g1, self.b1 = self._hex_to_rgb(start_color)
        self.r2, self.g2, self.b2 = self._hex_to_rgb(end_color)

        self.progress = 0.0
        self.draw()

    def _hex_to_rgb(self, hex_str):
        hex_str = hex_str.lstrip("#")
        return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))

    def set_progress(self, val):
        self.progress = max(0.0, min(1.0, val))
        self.draw()

    def draw(self):
        self.delete("all")
        # Фон прогресс-бара
        self.create_rectangle(
            0, 0, self.width, self.height, fill=self.bg_color, outline=""
        )

        # Заливка прогресса градиентом
        fill_width = int(self.width * self.progress)
        if fill_width > 0:
            for x in range(fill_width):
                ratio = x / self.width
                r = int(self.r1 + (self.r2 - self.r1) * ratio)
                g = int(self.g1 + (self.g2 - self.g1) * ratio)
                b = int(self.b1 + (self.b2 - self.b1) * ratio)
                color = f"#{r:02x}{g:02x}{b:02x}"
                self.create_line(x, 0, x, self.height, fill=color)


# --- Графический интерфейс Tkinter ---
class MetadataCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("METADATA PURGE — Очистка метаданных ИИ")
        self.root.geometry("700x550")
        self.root.resizable(False, False)

        # Настройка цветовой палитры (sleek dark mode)
        self.bg_main = "#0B0F19"  # Глубокий темный
        self.bg_card = "#1E293B"  # Серый сланец
        self.fg_main = "#F8FAFC"  # Белый/светлый текст
        self.fg_muted = "#94A3B8"  # Приглушенный текст
        self.accent_teal = "#2DD4BF"  # Неоновый бирюзовый
        self.accent_purple = "#a855f7"  # Неоновый фиолетовый

        self.root.configure(bg=self.bg_main)

        # Список файлов для обработки
        self.file_queue = []

        self._create_widgets()

        # Если файлы переданы через CLI аргументы при запуске GUI
        if len(sys.argv) > 1:
            self.add_paths(sys.argv[1:])

    def _create_widgets(self):
        # --- Заголовок ---
        header_frame = tk.Frame(self.root, bg=self.bg_main)
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        title_label = tk.Label(
            header_frame,
            text="🧬 METADATA PURGE",
            font=("Trebuchet MS", 18, "bold"),
            bg=self.bg_main,
            fg=self.accent_teal,
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            header_frame,
            text="Очистка EXIF, GPS и персональных тегов нейросетей",
            font=("Segoe UI", 10),
            bg=self.bg_main,
            fg=self.fg_muted,
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # --- Зона Drag & Drop / Click (Canvas) ---
        self.drop_canvas = tk.Canvas(
            self.root,
            bg=self.bg_card,
            height=120,
            highlightthickness=1,
            highlightbackground="#475569",
            bd=0,
        )
        self.drop_canvas.pack(fill="x", padx=20, pady=5)

        # Настройка Drag and Drop если библиотека доступна
        if HAS_DND:
            self.drop_canvas.drop_target_register(DND_FILES)
            self.drop_canvas.dnd_bind("<<Drop>>", self.handle_dnd_drop)
            dnd_text = "ПЕРЕТАЩИТЕ СЮДА ФАЙЛЫ ИЛИ ПАПКИ\n(или кликните для выбора)"
        else:
            dnd_text = (
                "КЛИКНИТЕ СЮДА ДЛЯ ВЫБОРА ФАЙЛОВ\n(drag-and-drop требует tkinterdnd2)"
            )

        self.drop_text_id = self.drop_canvas.create_text(
            330,
            60,
            text=dnd_text,
            font=("Segoe UI", 11, "bold"),
            fill=self.fg_main,
            justify="center",
        )

        self.drop_canvas.bind("<Button-1>", lambda e: self.browse_files())
        self.drop_canvas.bind(
            "<Enter>",
            lambda e: self.drop_canvas.configure(
                highlightbackground=self.accent_purple
            ),
        )
        self.drop_canvas.bind(
            "<Leave>",
            lambda e: self.drop_canvas.configure(highlightbackground="#475569"),
        )

        # --- Кнопки управления ---
        btn_frame = tk.Frame(self.root, bg=self.bg_main)
        btn_frame.pack(fill="x", padx=20, pady=10)

        # Стиль для кнопок
        btn_opts = {
            "font": ("Segoe UI", 10, "bold"),
            "bg": "#334155",
            "fg": self.fg_main,
            "activebackground": "#475569",
            "activeforeground": self.fg_main,
            "bd": 0,
            "padx": 15,
            "pady": 8,
            "cursor": "hand2",
        }

        self.btn_files = tk.Button(
            btn_frame, text="ВЫБРАТЬ ФАЙЛЫ", command=self.browse_files, **btn_opts
        )
        self.btn_files.pack(side="left")
        # Небольшой хак для отступа в tk pack
        self.btn_files.pack_configure(padx=(0, 10))

        self.btn_dir = tk.Button(
            btn_frame, text="ВЫБРАТЬ ПАПКУ", command=self.browse_directory, **btn_opts
        )
        self.btn_dir.pack(side="left")

        self.btn_clear_queue = tk.Button(
            btn_frame,
            text="ОЧИСТИТЬ СПИСОК",
            command=self.clear_queue,
            font=("Segoe UI", 10, "bold"),
            bg="#ef4444",
            fg=self.fg_main,
            activebackground="#dc2626",
            activeforeground=self.fg_main,
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2",
        )
        self.btn_clear_queue.pack(side="right")

        self.btn_start = tk.Button(
            btn_frame,
            text="ОЧИСТИТЬ МЕТАДАННЫЕ",
            command=self.process_queue,
            font=("Segoe UI", 10, "bold"),
            bg=self.accent_teal,
            fg="#0B0F19",
            activebackground="#0D9488",
            activeforeground="#0B0F19",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
        )
        self.btn_start.pack(side="right", padx=(0, 10))

        # --- Список файлов (Информация) ---
        self.info_label = tk.Label(
            self.root,
            text="Выбрано файлов: 0 (0.0 MB)",
            font=("Segoe UI", 9),
            bg=self.bg_main,
            fg=self.fg_muted,
        )
        self.info_label.pack(anchor="w", padx=20, pady=(0, 5))

        # --- Лог событий ---
        log_frame = tk.Frame(self.root, bg=self.bg_card)
        log_frame.pack(fill="both", expand=True, padx=20, pady=5)

        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side="right", fill="y")

        self.log_text = tk.Text(
            log_frame,
            bg="#080C14",
            fg=self.accent_teal,
            font=("Consolas", 9),
            yscrollcommand=scrollbar.set,
            bd=0,
            padx=10,
            pady=10,
        )
        self.log_text.pack(fill="both", expand=True)
        scrollbar.config(command=self.log_text.yview)

        # Делаем лог read-only
        self.log_text.config(state="disabled")

        # --- Прогресс-бар ---
        self.progress_bar = GradientProgressBar(
            self.root,
            width=660,
            height=8,
            bg_color="#1E293B",
            start_color=self.accent_purple,
            end_color=self.accent_teal,
        )
        self.progress_bar.pack(padx=20, pady=(10, 15))

        self.log("Приложение инициализировано. Готово к работе.")

    def log(self, message, level="INFO"):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{level}] {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def handle_dnd_drop(self, event):
        # tkinterdnd2 может возвращать пути в фигурных скобках, если они содержат пробелы
        raw_data = event.data
        paths = []

        # Парсинг путей (учитывая фигурные скобки для пробелов)
        import re

        # Находим элементы внутри скобок или просто слова
        parts = re.findall(r"{([^}]+)}|(\S+)", raw_data)
        for part in parts:
            path = part[0] if part[0] else part[1]
            if path:
                paths.append(path)

        self.add_paths(paths)

    def add_paths(self, paths):
        added_count = 0
        for path in paths:
            # Очищаем путь от возможных кавычек
            path = path.strip("\"'")
            if os.path.isdir(path):
                # Добавляем все изображения из папки
                for root_dir, _, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root_dir, file)
                        if self._is_supported_image(file_path):
                            if file_path not in self.file_queue:
                                self.file_queue.append(file_path)
                                added_count += 1
            elif os.path.isfile(path) and self._is_supported_image(path):
                if path not in self.file_queue:
                    self.file_queue.append(path)
                    added_count += 1

        if added_count > 0:
            self.log(f"Добавлено файлов в очередь: {added_count}")
            self.update_info_label()
        else:
            self.log(
                "Подходящие файлы изображений не найдены (поддерживаются JPG, PNG)",
                "WARNING",
            )

    def _is_supported_image(self, path):
        ext = os.path.splitext(path.lower())[1]
        # Проверяем, что файл не является уже очищенным
        if "_cleaned" in os.path.basename(path):
            return False
        return ext in (".jpg", ".jpeg", ".png")

    def update_info_label(self):
        total_size = 0.0
        for path in self.file_queue:
            try:
                total_size += os.path.getsize(path)
            except OSError:
                pass
        size_mb = total_size / (1024 * 1024)
        self.info_label.config(
            text=f"Выбрано файлов: {len(self.file_queue)} ({size_mb:.2f} MB)"
        )

    def browse_files(self):
        file_types = [("Изображения (*.jpg, *.png)", "*.jpg *.jpeg *.png")]
        files = filedialog.askopenfilenames(
            title="Выберите файлы для очистки", filetypes=file_types
        )
        if files:
            self.add_paths(files)

    def browse_directory(self):
        directory = filedialog.askdirectory(title="Выберите папку с изображениями")
        if directory:
            self.add_paths([directory])

    def clear_queue(self):
        self.file_queue.clear()
        self.update_info_label()
        self.progress_bar.set_progress(0.0)
        self.log("Очередь очищена.")

    def process_queue(self):
        if not self.file_queue:
            messagebox.showinfo(
                "Очередь пуста", "Пожалуйста, выберите файлы для очистки."
            )
            return

        self.log("Начало очистки метаданных...")
        self.root.update()

        total = len(self.file_queue)
        success_count = 0

        for index, path in enumerate(self.file_queue):
            dir_name, file_name = os.path.split(path)
            name, ext = os.path.splitext(file_name)
            output_name = f"{name}_cleaned{ext}"
            output_path = os.path.join(dir_name, output_name)

            self.log(f"Обработка: {file_name}...")
            self.root.update()

            success = clean_image(path, output_path)
            if success:
                success_count += 1
                self.log(f"Успешно очищен и сохранен как: {output_name}", "SUCCESS")
            else:
                self.log(f"Ошибка при обработке файла: {file_name}", "ERROR")

            # Обновление прогресс-бара
            progress_ratio = (index + 1) / total
            self.progress_bar.set_progress(progress_ratio)
            self.root.update()

        self.log(f"Обработка завершена! Успешно очищено: {success_count} из {total}.")
        messagebox.showinfo(
            "Готово",
            f"Очистка завершена!\nУспешно обработано: {success_count} из {total}.",
        )
        self.file_queue.clear()
        self.update_info_label()


# --- CLI режим работы ---
def run_cli():
    import argparse

    parser = argparse.ArgumentParser(description="Image Metadata Cleaner CLI")
    parser.add_argument("paths", nargs="+", help="Пути к файлам или папкам для очистки")
    args = parser.parse_args()

    print("🧬 Image Metadata Cleaner CLI")
    print("---------------------------------")

    file_queue = []
    for path in args.paths:
        if os.path.isdir(path):
            for root_dir, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    ext = os.path.splitext(file_path.lower())[1]
                    if ext in (".jpg", ".jpeg", ".png") and "_cleaned" not in file:
                        file_queue.append(file_path)
        elif os.path.isfile(path):
            ext = os.path.splitext(path.lower())[1]
            if ext in (".jpg", ".jpeg", ".png") and "_cleaned" not in path:
                file_queue.append(path)

    if not file_queue:
        print("Ошибка: Подходящие файлы изображений не найдены.")
        sys.exit(1)

    print(f"Найдено файлов для обработки: {len(file_queue)}")
    success_count = 0

    for path in file_queue:
        dir_name, file_name = os.path.split(path)
        name, ext = os.path.splitext(file_name)
        output_name = f"{name}_cleaned{ext}"
        output_path = os.path.join(dir_name, output_name)

        print(f"Обработка: {file_name}...", end="", flush=True)
        if clean_image(path, output_path):
            success_count += 1
            print(" [УСПЕШНО]")
        else:
            print(" [ОШИБКА]")

    print("---------------------------------")
    print(f"Завершено. Успешно очищено: {success_count} из {len(file_queue)}")


def main():
    # Если запуск без аргументов, либо аргументы не начинаются с файлов (например, запуск GUI с Рабочего стола)
    # но если передан аргумент --cli, то это CLI режим.
    if len(sys.argv) > 1 and "--cli" in sys.argv:
        # Удаляем --cli из аргументов перед CLI разбором
        sys.argv.remove("--cli")
        run_cli()
    else:
        if not HAS_TKINTER:
            print(
                "Ошибка: Графический интерфейс Tkinter недоступен в вашем окружении Python.",
                file=sys.stderr,
            )
            print(
                "Пожалуйста, запустите скрипт в CLI режиме, передав пути к файлам и аргумент '--cli'.",
                file=sys.stderr,
            )
            print(
                "Пример: python clean_image_metadata.py file.jpg --cli", file=sys.stderr
            )
            sys.exit(1)

        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            # Если переданы файлы напрямую (например, перетаскиванием на иконку скрипта),
            # то запускаем GUI с уже предзагруженными файлами.
            if HAS_DND:
                root = TkinterDnD.Tk()
            else:
                root = tk.Tk()
            app = MetadataCleanerApp(root)
            root.mainloop()
        else:
            # Стандартный запуск GUI
            if HAS_DND:
                root = TkinterDnD.Tk()
            else:
                root = tk.Tk()
            app = MetadataCleanerApp(root)
            root.mainloop()


if __name__ == "__main__":
    main()
