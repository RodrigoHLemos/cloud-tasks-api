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


def test_delete_task_success(client):
    created = client.post("/tasks", json={"title": "Tarefa para remover"}).json
    delete_res = client.delete(f'/tasks/{created["id"]}')
    assert delete_res.status_code == 204
    assert delete_res.data == b""
    assert client.get("/tasks").json == []


def test_delete_task_not_found(client):
    result = client.delete("/tasks/999")
    assert result.status_code == 404
    assert "error" in result.json


def test_filter_tasks_by_done(client):
    t1 = client.post("/tasks", json={"title": "Tarefa concluida"}).json
    client.post("/tasks", json={"title": "Tarefa pendente"})
    client.patch(f'/tasks/{t1["id"]}', json={"done": True})

    done_tasks = client.get("/tasks?done=true")
    assert done_tasks.status_code == 200
    assert len(done_tasks.json) == 1
    assert done_tasks.json[0]["title"] == "Tarefa concluida"

    pending_tasks = client.get("/tasks?done=false")
    assert pending_tasks.status_code == 200
    assert len(pending_tasks.json) == 1
    assert pending_tasks.json[0]["title"] == "Tarefa pendente"

    invalid_filter = client.get("/tasks?done=talvez")
    assert invalid_filter.status_code == 400


def test_version_endpoint(client):
    result = client.get("/version")
    assert result.status_code == 200
    assert result.json["service"] == "cloud-tasks-api"
    assert "version" in result.json
