import urllib.request

import pytest


def test_network_is_strictly_blocked():
    """Проверяет, что при попытке сетевого запроса в тестах выбрасывается ошибка блокировки сокета."""
    # Пытаемся сделать реальный HTTP-запрос к внешнему сайту
    with pytest.raises(Exception) as excinfo:
        urllib.request.urlopen("https://example.com", timeout=2.0)

    # Ошибка должна указывать на то, что сокет заблокирован плагином pytest-socket
    err_msg = str(excinfo.value)
    assert (
        "A test tried to use socket" in err_msg
        or "SocketBlockedError" in excinfo.type.__name__
    )
