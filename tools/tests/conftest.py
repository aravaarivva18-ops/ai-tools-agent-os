from pytest_socket import _STASH_KEY


def pytest_runtest_setup(item):
    if _STASH_KEY in item.config.stash:
        item.config.stash[_STASH_KEY].allow_unix_socket = True
