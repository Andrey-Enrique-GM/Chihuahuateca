import pytest
import app as app_module
from entities.elemento import Elemento
from entities.log import Log
from entities.usuario import User



@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(app_module.app.config, "TESTING", True)
    monkeypatch.setitem(app_module.app.config, "SECRET_KEY", "test-secret")
    return app_module.app.test_client()


@pytest.fixture
def authenticated_client(client):
    with client.session_transaction() as session:
        session["usuario_id"] = 1
        session["username"] = "test-user"
        session["nombre"] = "Usuario de prueba"
        session["rol"] = "USER"
    return client


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


def test_create_element(authenticated_client, monkeypatch):
    saved_elements = []
    monkeypatch.setattr(
        Elemento,
        "save",
        staticmethod(lambda **kwargs: saved_elements.append(kwargs) or True),
    )
    monkeypatch.setattr(Log, "save_log", staticmethod(lambda *args: None))

    response = authenticated_client.post(
        "/api/guardar",
        json={
            "titulo": "Libro de prueba",
            "tipo": "libro",
            "autor_director": "Autor de prueba",
            "genero": "Ficción",
            "descripcion": "Descripción",
            "calificacion": 4,
            "opinion": "Buena lectura",
        },
    )

    assert response.status_code == 200
    assert response.json["success"] is True
    assert len(saved_elements) == 1
    assert saved_elements[0]["titulo"] == "Libro de prueba"
    assert saved_elements[0]["usuario_id"] == 1


def test_update_element(authenticated_client, monkeypatch):
    updated_elements = []
    monkeypatch.setattr(
        Elemento,
        "update",
        staticmethod(lambda **kwargs: updated_elements.append(kwargs) or True),
    )
    monkeypatch.setattr(Log, "save_log", staticmethod(lambda *args: None))

    response = authenticated_client.post(
        "/api/editar",
        json={
            "id": 42,
            "titulo": "Libro actualizado",
            "tipo": "libro",
            "autor_director": "Autor de prueba",
            "genero": "Ficción",
            "descripcion": "Descripción actualizada",
            "calificacion": 5,
            "opinion": "Excelente lectura",
        },
    )

    assert response.status_code == 200
    assert response.json["success"] is True
    assert len(updated_elements) == 1
    assert updated_elements[0]["id_elemento"] == 42
    assert updated_elements[0]["titulo"] == "Libro actualizado"
    assert updated_elements[0]["usuario_id"] == 1


def test_delete_element(authenticated_client, monkeypatch):
    deleted_elements = []
    monkeypatch.setattr(
        Elemento,
        "delete",
        staticmethod(lambda **kwargs: deleted_elements.append(kwargs) or True),
    )
    monkeypatch.setattr(Log, "save_log", staticmethod(lambda *args: None))

    response = authenticated_client.delete("/api/borrar/42")

    assert response.status_code == 200
    assert response.json["success"] is True
    assert deleted_elements == [{"id_elemento": 42, "usuario_id": 1, "user_role": "USER"}]
