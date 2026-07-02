import datetime
import json
import os
import pathlib
import sys

DEFAULT_CONFIG = {
    "version": "1.0.0",
    "vault": {"handoffs_dir": "vault/handoffs", "findings_file": "vault/findings.md"},
    "ui": {"design_md": "DESIGN.md", "theme_css": "theme.css"},
    "healer": {"test_command": "pytest", "exclude_logs": ["*.tmp", "*.log"]},
}


def get_workspace_root() -> pathlib.Path:
    """Находит ближайший корень проекта (наличие .git, package.json, .agents или .agentic-dev.json)."""
    current = pathlib.Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (
            (parent / ".git").exists()
            or (parent / ".agents").exists()
            or (parent / "package.json").exists()
            or (parent / ".agentic-dev.json").exists()
        ):
            return parent
    # Фолбэк: если запущен из папки tools, родителем будет корень
    if current.name == "tools":
        return current.parent
    return current


def get_global_config_dir() -> pathlib.Path:
    """Возвращает платформо-зависимый путь для глобальных настроек."""
    home = pathlib.Path.home()
    if sys.platform == "win32":
        return (
            pathlib.Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
            / "agentic-dev"
        )
    elif sys.platform == "darwin":
        return home / "Library/Application Support/agentic-dev"
    else:
        return home / ".config" / "agentic-dev"


def load_config() -> dict:
    """Загружает .agentic-dev.json из корня проекта, дополняя дефолтными значениями."""
    root = get_workspace_root()
    config_file = root / ".agentic-dev.json"

    # Делаем глубокую копию, чтобы избежать мутаций
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    if config_file.exists():
        try:
            from tools.json_utils import safe_load_json
            with open(config_file, encoding="utf-8") as f:
                user_config = safe_load_json(f.read())
                if isinstance(user_config, dict):
                    # Рекурсивно сливаем словари, чтобы не затереть неполные секции
                    for key, val in user_config.items():
                        if (
                            isinstance(val, dict)
                            and key in config
                            and isinstance(config[key], dict)
                        ):
                            config[key].update(val)
                        else:
                            config[key] = val
        except Exception as e:
            print(
                f"⚠️ Ошибка чтения файла конфигурации {config_file}: {e}",
                file=sys.stderr,
            )

    return config


GLOBAL_CONFIG_FILENAME = "config.json"
GUMROAD_PRODUCT_PERMALINK = "antigravity-ai-tools"
LICENSE_CACHE_DAYS = 7


def get_global_config_path() -> pathlib.Path:
    """Возвращает путь к глобальному файлу конфигурации."""
    return get_global_config_dir() / GLOBAL_CONFIG_FILENAME


def load_global_config() -> dict:
    """Загружает глобальные настройки из config.json."""
    path = get_global_config_path()
    if path.exists():
        try:
            from tools.json_utils import safe_load_json
            with open(path, encoding="utf-8") as f:
                res = safe_load_json(f.read())
                return res if isinstance(res, dict) else {}
        except Exception:
            pass
    return {}


def save_global_config(config_data: dict) -> None:
    """Сохраняет глобальные настройки в config.json."""
    path = get_global_config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Не удалось сохранить глобальный конфиг: {e}", file=sys.stderr)


def verify_license_online(key: str) -> tuple[bool, bool]:
    """
    Проверяет ключ через Gumroad API.
    Возвращает (is_valid, is_network_error).
    """
    import urllib.error
    import urllib.parse
    import urllib.request

    url = "https://api.gumroad.com/v2/licenses/verify"
    payload = {"product_permalink": GUMROAD_PRODUCT_PERMALINK, "license_key": key}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        from tools.json_utils import safe_load_json
        with urllib.request.urlopen(req, timeout=2.0) as response:
            if response.status == 200:
                res_data = safe_load_json(response.read().decode("utf-8"))
                success = res_data.get("success", False) if isinstance(res_data, dict) else False
                purchase = res_data.get("purchase", {}) if isinstance(res_data, dict) else {}
                refunded = purchase.get("refunded", False)
                chargebacked = purchase.get("chargebacked", False)

                if success and not refunded and not chargebacked:
                    return True, False
            return False, False
    except urllib.error.HTTPError as e:
        if e.code in (404, 422):
            try:
                from tools.json_utils import safe_load_json
                res_data = safe_load_json(e.read().decode("utf-8"))
                if isinstance(res_data, dict) and not res_data.get("success", False):
                    return False, False
            except Exception:
                pass
            return False, False
        return False, True
    except (TimeoutError, urllib.error.URLError, ConnectionError):
        return False, True
    except Exception:
        return False, True


def check_license_status() -> tuple[bool, str]:
    """
    Проверяет статус лицензии.
    Возвращает (is_allowed, status_code).
    """
    # 1. Поиск ключа
    key = os.environ.get("AGY_LICENSE_KEY")
    if not key:
        local_cfg = load_config()
        key = local_cfg.get("license_key")

    global_cfg = load_global_config()
    if not key:
        key = global_cfg.get("license_key")

    if not key:
        return False, "missing"

    # 2. Проверка кэша
    cached_key = global_cfg.get("license_key")
    cached_time_str = global_cfg.get("license_verified_at")

    if cached_key == key and cached_time_str:
        try:
            cached_time = datetime.datetime.fromisoformat(cached_time_str)
            days_passed = (datetime.datetime.now() - cached_time).days
            if days_passed < LICENSE_CACHE_DAYS:
                return True, "cached"
        except Exception:
            pass

    # 3. Сетевая проверка
    is_valid, is_net_error = verify_license_online(key)

    if is_valid:
        global_cfg["license_key"] = key
        global_cfg["license_verified_at"] = datetime.datetime.now().isoformat()
        save_global_config(global_cfg)
        return True, "verified"

    if is_net_error:
        if cached_key == key:
            return True, "offline_grace"
        return False, "network_error"

    if cached_key == key:
        global_cfg.pop("license_key", None)
        global_cfg.pop("license_verified_at", None)
        save_global_config(global_cfg)

    return False, "invalid"
