import pytest
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    return app.test_client()


def test_health(client):
    result = client.get("/health")
    assert result.status_code == 200
    assert result.json["status"] == "ok"


def test_create_and_list(client):
    result = client.post("/tasks", json={"title": "Estudar GitHub Actions"})
    assert result.status_code == 201
    assert result.json["id"] == 1
    listed = client.get("/tasks")
    assert listed.status_code == 200
    assert len(listed.json) == 1
    assert listed.json[0]["title"] == "Estudar GitHub Actions"


def test_invalid_title(client):
    assert client.post("/tasks", json={"title": "  "}).status_code == 400


def test_mark_done(client):
    item = client.post("/tasks", json={"title": "Deploy"}).json
    result = client.patch(f'/tasks/{item["id"]}', json={"done": True})
    assert result.status_code == 200
    assert client.get("/tasks").json[0]["done"] is True


def test_not_found(client):
    assert client.patch("/tasks/999", json={"done": True}).status_code == 404


def test_update_title(client):
    item = client.post("/tasks", json={"title": "Titulo antigo"}).json
    result = client.patch(f'/tasks/{item["id"]}', json={"title": "  Titulo novo  "})
    assert result.status_code == 200
    assert result.json == {"id": item["id"], "title": "Titulo novo", "done": False}
    assert client.get("/tasks").json[0]["title"] == "Titulo novo"


def test_update_title_keeps_done(client):
    item = client.post("/tasks", json={"title": "Tarefa"}).json
    client.patch(f'/tasks/{item["id"]}', json={"done": True})
    result = client.patch(f'/tasks/{item["id"]}', json={"title": "Tarefa renomeada"})
    assert result.status_code == 200
    assert result.json["done"] is True


def test_update_title_and_done_together(client):
    item = client.post("/tasks", json={"title": "Tarefa"}).json
    result = client.patch(f'/tasks/{item["id"]}', json={"title": "Concluida", "done": True})
    assert result.status_code == 200
    assert result.json == {"id": item["id"], "title": "Concluida", "done": True}


@pytest.mark.parametrize("title", ["", "   ", 123, None, "x" * 121])
def test_update_invalid_title(client, title):
    item = client.post("/tasks", json={"title": "Original"}).json
    result = client.patch(f'/tasks/{item["id"]}', json={"title": title})
    assert result.status_code == 400
    assert client.get("/tasks").json[0]["title"] == "Original"


def test_update_without_fields(client):
    item = client.post("/tasks", json={"title": "Original"}).json
    assert client.patch(f'/tasks/{item["id"]}', json={}).status_code == 400


def test_update_title_not_found(client):
    result = client.patch("/tasks/999", json={"title": "Inexistente"})
    assert result.status_code == 404
    assert result.json["error"] == "tarefa nao encontrada"


def test_delete_task(client):
    item = client.post("/tasks", json={"title": "Remover"}).json
    result = client.delete(f'/tasks/{item["id"]}')
    assert result.status_code == 204
    assert result.data == b""
    assert client.get("/tasks").json == []


def test_delete_not_found(client):
    result = client.delete("/tasks/999")
    assert result.status_code == 404
    assert result.json["error"] == "tarefa nao encontrada"


def test_delete_twice_returns_not_found(client):
    item = client.post("/tasks", json={"title": "Remover duas vezes"}).json
    assert client.delete(f'/tasks/{item["id"]}').status_code == 204
    assert client.delete(f'/tasks/{item["id"]}').status_code == 404
