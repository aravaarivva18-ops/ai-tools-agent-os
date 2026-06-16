---
name: vps-automation
description: Best practices for SSH remote VPS execution and Cloudflare DNS automation using Python.
---

# Автоматизация VPS и Cloudflare DNS (Stealth Infrastructure)

Этот навык описывает стандарты для автоматизации развертывания приложений на удаленных серверах (VPS) по протоколу SSH и управления DNS-записями через Cloudflare API на Python.

## 🔑 1. Безопасное SSH-соединение (SSH Key & Keypair)

Для автоматизации удаленных команд используется библиотека `paramiko` или `fabric`. Пароли не используются; все сессии должны авторизовываться через SSH-ключи (желательно с поддержкой passphrase).

### Паттерн безопасного подключения:
```python
import paramiko
from pathlib import Path

def execute_remote_cmd(
    ip: str, 
    username: str, 
    cmd: str, 
    key_path: Path, 
    passphrase: str | None = None
) -> str:
    """Выполняет команду на удаленном VPS по SSH."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Загрузка приватного ключа
    private_key = paramiko.RSAKey.from_private_key_file(
        str(key_path), 
        password=passphrase
    )
    
    try:
        client.connect(
            hostname=ip, 
            username=username, 
            pkey=private_key, 
            timeout=15
        )
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            return stdout.read().decode("utf-8")
        else:
            return f"Error (Exit {exit_status}): {stderr.read().decode('utf-8')}"
            
    finally:
        client.close()
```

---

## 🌐 2. Автоматизация Cloudflare DNS & SSL

Для интеграции домена и выпуска SSL сертификатов используется официальный SDK `cloudflare` (или прямой вызов REST API через `requests`/`curl_cffi`).

### Паттерн создания DNS A-записи с Proxy:
```python
import requests
from typing import Dict, Any

def create_cloudflare_dns_record(
    zone_id: str, 
    api_token: str, 
    subdomain: str, 
    ip: str, 
    proxied: bool = True
) -> Dict[str, Any]:
    """Создает A-запись в Cloudflare."""
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "type": "A",
        "name": subdomain,
        "content": ip,
        "ttl": 1,  # Auto
        "proxied": proxied
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
```

### Настройка SSL режима (Strict Mode):
Для обеспечения максимальной безопасности трафика между Cloudflare и вашим VPS (например, при использовании панели управления или Xray):
```python
def set_cloudflare_ssl_strict(zone_id: str, api_token: str) -> bool:
    """Устанавливает режим SSL в 'strict'."""
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/ssl"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    payload = {"value": "strict"}
    
    response = requests.patch(url, json=payload, headers=headers, timeout=10)
    return response.status_code == 200
```

---

## 🏗️ 3. Принципы развертывания инфраструктуры
1. **Decoupled Architecture:** Скрипт-инициализатор работает локально (на Mac разработчика) как контроллер, а сервер VPS является чистым хостом. Вся логика, ключи API и токены хранятся исключительно локально в `.env`.
2. **Предварительные проверки (Sanity Checks):** Перед выполнением любых удаленных деплой-команд скрипт обязан верифицировать:
   * Доступность хоста по SSH (порт 22).
   * Валидность Cloudflare API токена.
   * Отсутствие дублирующих DNS-записей для избежания конфликтов.
