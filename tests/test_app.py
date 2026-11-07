import pytest
import app as app_module
from entities.log import Log
from entities.usuario import User



@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(app_module.app.config, "TESTING", True)
    monkeypatch.setitem(app_module.app.config, "SECRET_KEY", "test-secret")
    return app_module.app.test_client()


def test_login_starts_session(client, monkeypatch):
    usuario = User(
        id=1,
        username="test-user",
        nombre="Usuario de prueba",
        password="",
        rol="USER",
        zona_horaria="AUTO",
    )
    monkeypatch.setattr(
        User,
        "authenticate",
        staticmethod(lambda username, password: usuario),
    )
    monkeypatch.setattr(Log, "save_log", staticmethod(lambda *args: None))

    response = client.post(
        "/api/login",
        json={"username": "test-user", "password": "password"},
    )

    assert response.status_code == 200
    assert response.json["success"] is True
    with client.session_transaction() as session:
        assert session["usuario_id"] == usuario.id
        assert session["username"] == usuario.username


def test_logout_clears_session(client, monkeypatch):
    monkeypatch.setattr(Log, "save_log", staticmethod(lambda *args: None))
    with client.session_transaction() as session:
        session["usuario_id"] = 1
        session["username"] = "test-user"
        session["nombre"] = "Usuario de prueba"

    response = client.get("/logout")
    
    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    with client.session_transaction() as session:
        assert not session
