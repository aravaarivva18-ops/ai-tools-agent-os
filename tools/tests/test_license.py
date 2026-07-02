#!/usr/bin/env python3
import datetime
import json
import urllib.error
from unittest import mock

try:
    from tools import config
except ImportError:
    import config


def test_verify_license_online_success():
    """Тест успешной онлайн проверки ключа."""
    mock_response = mock.MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.status = 200
    mock_response.read.return_value = json.dumps(
        {
            "success": True,
            "uses": 1,
            "purchase": {"refunded": False, "chargebacked": False},
        }
    ).encode("utf-8")

    with mock.patch("urllib.request.urlopen", return_value=mock_response):
        is_valid, is_net_error = config.verify_license_online("VALID-KEY")
        assert is_valid is True
        assert is_net_error is False


def test_verify_license_online_invalid():
    """Тест онлайн проверки невалидного ключа."""
    # Gumroad возвращает HTTP 404/422 при невалидном ключе
    mock_err = urllib.error.HTTPError(
        url="https://api.gumroad.com/v2/licenses/verify",
        code=404,
        msg="Not Found",
        hdrs=None,
        fp=mock.MagicMock(),
    )
    mock_err.fp.read.return_value = json.dumps(
        {"success": False, "message": "License not found"}
    ).encode("utf-8")

    with mock.patch("urllib.request.urlopen", side_effect=mock_err):
        is_valid, is_net_error = config.verify_license_online("INVALID-KEY")
        assert is_valid is False
        assert is_net_error is False


def test_verify_license_online_network_error():
    """Тест онлайн проверки при сбое сети."""
    with mock.patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("Connection refused"),
    ):
        is_valid, is_net_error = config.verify_license_online("ANY-KEY")
        assert is_valid is False
        assert is_net_error is True


def test_check_license_status_missing(tmp_path, monkeypatch):
    """Тест статуса лицензии, если ключ отсутствует."""
    # Подменяем пути к конфигам на временные, чтобы не портить настоящие настройки
    global_cfg_path = tmp_path / "global_config.json"
    monkeypatch.setattr("tools.config.get_global_config_path", lambda: global_cfg_path)

    # Удаляем переменную окружения, если она есть
    monkeypatch.delenv("AGY_LICENSE_KEY", raising=False)

    # Подменяем локальный конфиг на пустой
    with mock.patch("tools.config.load_config", return_value={}):
        allowed, status = config.check_license_status()
        assert allowed is False
        assert status == "missing"


def test_check_license_status_cached(tmp_path, monkeypatch):
    """Тест статуса лицензии, если есть валидный локальный кэш."""
    global_cfg_path = tmp_path / "global_config.json"
    monkeypatch.setattr("tools.config.get_global_config_path", lambda: global_cfg_path)
    monkeypatch.delenv("AGY_LICENSE_KEY", raising=False)

    # Сохраняем валидный кэш (время верификации - вчера)
    verified_at = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
    config.save_global_config(
        {"license_key": "GOOD-KEY", "license_verified_at": verified_at}
    )

    with mock.patch(
        "tools.config.load_config", return_value={"license_key": "GOOD-KEY"}
    ):
        allowed, status = config.check_license_status()
        assert allowed is True
        assert status == "cached"


def test_check_license_status_offline_grace(tmp_path, monkeypatch):
    """Тест офлайн-режима (grace period) при сбое сети для ранее кэшированного ключа."""
    global_cfg_path = tmp_path / "global_config.json"
    monkeypatch.setattr("tools.config.get_global_config_path", lambda: global_cfg_path)
    monkeypatch.delenv("AGY_LICENSE_KEY", raising=False)

    # Записываем устаревший кэш (10 дней назад)
    verified_at = (datetime.datetime.now() - datetime.timedelta(days=10)).isoformat()
    config.save_global_config(
        {"license_key": "GOOD-KEY", "license_verified_at": verified_at}
    )

    # Имитируем сетевую ошибку
    with mock.patch(
        "tools.config.load_config", return_value={"license_key": "GOOD-KEY"}
    ):
        with mock.patch(
            "tools.config.verify_license_online", return_value=(False, True)
        ):
            allowed, status = config.check_license_status()
            assert allowed is True
            assert status == "offline_grace"
