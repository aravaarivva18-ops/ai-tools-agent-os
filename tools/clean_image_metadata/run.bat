@echo off
:: Установка кодировки UTF-8 для корректного отображения русского текста
chcp 65001 > nul

echo ======================================================
echo  🧬 METADATA PURGE — Очиститель метаданных картинок
echo ======================================================

:: 1. Проверяем, установлен ли Python в системе
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не обнаружен в вашей системе!
    echo.
    echo Для работы программы необходимо установить Python:
    echo 1. Скачайте установщик с сайта https://www.python.org/downloads/
    echo 2. При установке ОБЯЗАТЕЛЬНО поставьте галочку "Add Python to PATH".
    echo.
    pause
    exit /b
)

:: 2. Проверяем и устанавливаем библиотеки Pillow и piexif при необходимости
python -c "import PIL, piexif" >nul 2>nul
if %errorlevel% neq 0 (
    echo [ИНФО] Установка необходимых библиотек (Pillow, piexif)...
    python -m pip install --upgrade pip
    python -m pip install Pillow piexif
    if %errorlevel% neq 0 (
        echo [ОШИБКА] Не удалось установить библиотеки автоматически.
        echo Попробуйте запустить командную строку от имени Администратора
        echo и выполнить команду: pip install Pillow piexif
        pause
        exit /b
    )
    echo [УСПЕШНО] Библиотеки установлены!
)

:: 3. Запуск программы
:: Если файлы перетащили на .bat (%* содержит пути к файлам),
:: то передаем их аргументами в Python.
:: Если запустили простым двойным кликом (аргументов нет), 
:: запускаем GUI через pythonw, чтобы скрыть черное окно консоли.
if "%~1" == "" (
    echo [ИНФО] Запуск графического интерфейса...
    start "" pythonw "%~dp0clean_image_metadata.py"
) else (
    echo [ИНФО] Обработка перетащенных файлов...
    python "%~dp0clean_image_metadata.py" %*
    echo.
    echo [ГОТОВО] Все файлы обработаны!
    timeout /t 5
)
