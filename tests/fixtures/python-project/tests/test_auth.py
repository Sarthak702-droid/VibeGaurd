from src.auth import login


def test_login() -> None:
    assert login("test")
