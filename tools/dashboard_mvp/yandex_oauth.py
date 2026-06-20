from datetime import datetime, timedelta

import httpx
from dashboard_mvp.config import (
    YANDEX_CLIENT_ID,
    YANDEX_CLIENT_SECRET,
    YANDEX_REDIRECT_URI,
)

YANDEX_OAUTH_URL = "https://oauth.yandex.ru"

def get_yandex_auth_url(project_id: int) -> str:
    """Генерирует URL-адрес для авторизации в Яндекс.ID с передачей project_id в state."""
    # Используем state, чтобы передать ID проекта сквозь процесс авторизации
    return (
        f"{YANDEX_OAUTH_URL}/authorize?"
        f"response_type=code"
        f"&client_id={YANDEX_CLIENT_ID}"
        f"&redirect_uri={YANDEX_REDIRECT_URI}"
        f"&state={project_id}"
    )

async def exchange_code_for_tokens(code: str) -> dict:
    """Обменивает временный authorization code на access_token и refresh_token."""
    url = f"{YANDEX_OAUTH_URL}/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": YANDEX_CLIENT_ID,
        "client_secret": YANDEX_CLIENT_SECRET
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)

    if response.status_code != 200:
        raise Exception(f"Ошибка Яндекс OAuth ({response.status_code}): {response.text}")

    res_data = response.json()
    expires_in = res_data.get("expires_in", 31536000) # По умолчанию 1 год в секундах
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    return {
        "access_token": res_data["access_token"],
        "refresh_token": res_data.get("refresh_token"),
        "expires_at": expires_at
    }

async def refresh_yandex_token(refresh_token: str) -> dict:
    """Обновляет access_token с помощью refresh_token."""
    url = f"{YANDEX_OAUTH_URL}/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": YANDEX_CLIENT_ID,
        "client_secret": YANDEX_CLIENT_SECRET
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)

    if response.status_code != 200:
        raise Exception(f"Ошибка обновления токена Яндекс ({response.status_code}): {response.text}")

    res_data = response.json()
    expires_in = res_data.get("expires_in", 31536000)
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    return {
        "access_token": res_data["access_token"],
        "refresh_token": res_data.get("refresh_token", refresh_token),
        "expires_at": expires_at
    }
