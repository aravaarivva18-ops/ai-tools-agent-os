#!/bin/bash
set -e

# Оформление вывода
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PLAIN='\033[0m'

echo -e "${BOLD}=== Antigravity AI-Tools CLI Installation ===${PLAIN}"

# 1. Проверка uv
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ Ошибка: Менеджер пакетов 'uv' не обнаружен.${PLAIN}"
    echo "Пожалуйста, установите 'uv' перед запуском этого скрипта:"
    echo "https://github.com/astral-sh/uv"
    exit 1
else
    echo "✅ Обнаружен uv. Синхронизируем зависимости..."
    uv sync --all-packages
fi

# 2. Инициализация файла конфигурации
echo "⚙️ Инициализация конфигурации проекта..."
if [ -f "tools/cli.py" ]; then
    uv run python tools/cli.py init
else
    echo -e "${RED}❌ Ошибка: Скрипт tools/cli.py не найден в текущей папке.${PLAIN}"
    echo "Убедитесь, что вы запускаете install.sh из корня проекта ai-tools."
    exit 1
fi

# 3. Настройка исполняемого файла
CURRENT_DIR=$(pwd)
CLI_PATH="$CURRENT_DIR/tools/cli.py"
chmod +x "$CLI_PATH"

# 4. Регистрация глобального alias
ALIAS_CMD="alias agy=\"python3 '$CLI_PATH'\""
SHELL_CONFIG=""

# Определение файла конфигурации шелла
if [[ "$SHELL" == */zsh ]]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [[ "$SHELL" == */bash ]]; then
    SHELL_CONFIG="$HOME/.bashrc"
fi

if [ -n "$SHELL_CONFIG" ]; then
    if [ -f "$SHELL_CONFIG" ] && grep -q "alias agy=" "$SHELL_CONFIG"; then
        echo -e "${YELLOW}ℹ️ Псевдоним 'agy' уже зарегистрирован в $SHELL_CONFIG.${PLAIN}"
    else
        echo "" >> "$SHELL_CONFIG"
        echo "# Antigravity AI-Tools CLI" >> "$SHELL_CONFIG"
        echo "$ALIAS_CMD" >> "$SHELL_CONFIG"
        echo -e "${GREEN}✅ Псевдоним 'agy' успешно добавлен в $SHELL_CONFIG.${PLAIN}"
        echo -e "Выполните команду для обновления терминала: ${BOLD}source $SHELL_CONFIG${PLAIN}"
    fi
else
    echo -e "${YELLOW}⚠️ Не удалось определить файл конфигурации вашей оболочки ($SHELL).${PLAIN}"
    echo -e "Вы можете вручную добавить следующий alias в файл настроек вашего терминала:"
    echo -e "  ${BOLD}$ALIAS_CMD${PLAIN}"
fi

echo -e "\n${GREEN}🎉 Установка успешно завершена!${PLAIN}"
echo -e "Доступные команды:"
echo -e "  - ${BOLD}agy init${PLAIN}   : Инициализировать конфигурацию .agentic-dev.json"
echo -e "  - ${BOLD}agy run${PLAIN}    : Запустить авто-лечение ошибок"
echo -e "  - ${BOLD}agy search${PLAIN} : Семантический поиск по памяти"
