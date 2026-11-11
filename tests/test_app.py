import pytest
import app as app_module
from entities.element import Element
from entities.log import Log
from entities.user import User



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
    user = User(
        id=1,
        username="test-user",
        name="Usuario de prueba",
        password="",
        role="USER",
        timezone="AUTO",
    )
    monkeypatch.setattr(
        User,
        "authenticate",
        staticmethod(lambda username, password: user),
    )
    monkeypatch.setattr(Log, "save_log", staticmethod(lambda *args: None))

    response = client.post(
        "/api/login",
        json={"username": "test-user", "password": "password"},
    )

    assert response.status_code == 200
    assert response.json["success"] is True
    with client.session_transaction() as session:
        assert session["usuario_id"] == user.id
        assert session["username"] == user.username


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
        Element,
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
    assert saved_elements[0]["title"] == "Libro de prueba"
    assert saved_elements[0]["user_id"] == 1


def test_update_element(authenticated_client, monkeypatch):
    updated_elements = []
    monkeypatch.setattr(
        Element,
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
    assert updated_elements[0]["element_id"] == 42
    assert updated_elements[0]["title"] == "Libro actualizado"
    assert updated_elements[0]["user_id"] == 1


def test_delete_element(authenticated_client, monkeypatch):
    deleted_elements = []
    monkeypatch.setattr(
        Element,
        "delete",
        staticmethod(lambda **kwargs: deleted_elements.append(kwargs) or True),
    )
    monkeypatch.setattr(Log, "save_log", staticmethod(lambda *args: None))

    response = authenticated_client.delete("/api/borrar/42")

    assert response.status_code == 200
    assert response.json["success"] is True
    assert deleted_elements == [{"element_id": 42, "user_id": 1, "user_role": "USER"}]


def test_index_renders_elements(authenticated_client, monkeypatch):
    sample_element = Element(
        id=1,
        title="Don Quijote",
        element_type="libro",
        author_director="Miguel de Cervantes",
        genre="Novela",
        description="El ingenioso hidalgo",
        rating=5,
        review="Obra cumbre",
        user_id=1,
        user_name="Usuario de prueba",
        created_at="2026-01-01 12:00:00",
        updated_at="2026-01-01 12:00:00",
        image_url="https://example.com/cover.jpg",
        total_likes=3,
        user_likes=True,
        user_username="test-user",
        user_follows_creator=False,
    )
    monkeypatch.setattr(Element, "get_all", staticmethod(lambda *args, **kwargs: [sample_element]))

    response = authenticated_client.get("/coleccion")
    assert response.status_code == 200
    assert "Don Quijote" in response.get_data(as_text=True)
    assert "Miguel de Cervantes" in response.get_data(as_text=True)


def test_profile_renders(authenticated_client, monkeypatch):
    user = User(id=1, username="test-user", name="Usuario de prueba", password="", role="USER", timezone="AUTO")
    monkeypatch.setattr(User, "get_by_id", staticmethod(lambda uid: user))
    monkeypatch.setattr(Log, "get_by_user", staticmethod(lambda uid: []))
    monkeypatch.setattr(Element, "get_all", staticmethod(lambda *args, **kwargs: []))

    class DummyCursor:
        def execute(self, *args, **kwargs): pass
        def fetchone(self): return {'total': 0}
        def close(self): pass
    class DummyConnection:
        def cursor(self, *args, **kwargs): return DummyCursor()
        def close(self): pass
    monkeypatch.setattr(app_module, "get_connection", lambda: DummyConnection())

    response = authenticated_client.get("/profile")
    assert response.status_code == 200
    assert "Usuario de prueba" in response.get_data(as_text=True)


def test_users_renders(authenticated_client, monkeypatch):
    test_user = User(
        id=1,
        username='test-user',
        name='Usuario de prueba',
        password='',
        role='USER',
        timezone='AUTO',
        registration_date='2026-01-01',
        is_following=False
    )
    test_user2 = User(
        id=2,
        username='other-user',
        name='Otro Usuario',
        password='',
        role='ADMIN',
        timezone='-7',
        registration_date='2026-02-01',
        is_following=True
    )
    monkeypatch.setattr(User, "get_all", staticmethod(lambda *args: [test_user, test_user2]))

    response = authenticated_client.get("/users")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Usuario de prueba" in html
    assert "Otro Usuario" in html
    assert "2 usuarios" in html
    assert "✓ Siguiendo" in html


def test_index_renders_empty(authenticated_client, monkeypatch):
    monkeypatch.setattr(Element, "get_all", staticmethod(lambda *args, **kwargs: []))

    response = authenticated_client.get("/coleccion")
    assert response.status_code == 200
    assert "La Chihuahuateca está vacía" in response.get_data(as_text=True)


def test_profile_renders_with_stats_and_logs(authenticated_client, monkeypatch):
    user = User(id=1, username="test-user", name="Usuario de prueba", password="", role="USER", timezone="-7")
    monkeypatch.setattr(User, "get_by_id", staticmethod(lambda uid: user))

    sample_element = Element(
        id=10,
        title="1984",
        element_type="libro",
        author_director="George Orwell",
        rating=5,
        user_id=1,
    )
    sample_element2 = Element(
        id=11,
        title="Inception",
        element_type="pelicula",
        author_director="Christopher Nolan",
        rating=4,
        user_id=1,
    )
    sample_element3 = Element(
        id=12,
        title="Breaking Bad",
        element_type="serie",
        author_director="Vince Gilligan",
        rating=5,
        user_id=1,
    )
    monkeypatch.setattr(Element, "get_all", staticmethod(lambda *args, **kwargs: [sample_element, sample_element2, sample_element3]))

    from datetime import datetime, timezone
    sample_log = Log(
        id=1,
        timestamp=datetime.now(timezone.utc),
        user=user,
        description="Guardó el elemento '1984'",
        log_type=app_module.LogType.SAVE,
        details=""
    )
    monkeypatch.setattr(Log, "get_by_user", staticmethod(lambda uid: [sample_log]))

    class DummyCursor:
        def execute(self, *args, **kwargs): pass
        def fetchone(self): return {'total': 5}
        def close(self): pass
    class DummyConnection:
        def cursor(self, *args, **kwargs): return DummyCursor()
        def close(self): pass
    monkeypatch.setattr(app_module, "get_connection", lambda: DummyConnection())

    response = authenticated_client.get("/profile")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Usuario de prueba" in html
    assert "Guardó el elemento" in html
