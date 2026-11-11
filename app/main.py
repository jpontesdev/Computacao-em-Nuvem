import os
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request

DB_PATH = os.environ.get("DB_PATH", "/tmp/cloud_tasks.db")
TITLE_MAX_LENGTH = 120


def validate_title(value):
    if not isinstance(value, str) or not value.strip():
        return None, "title deve ser texto nao vazio"
    title = value.strip()
    if len(title) > TITLE_MAX_LENGTH:
        return None, f"title excede {TITLE_MAX_LENGTH} caracteres"
    return title, None


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(DATABASE=DB_PATH)
    if test_config:
        app.config.update(test_config)

    def connect():
        path = Path(app.config["DATABASE"])
        path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(str(path))
        db.row_factory = sqlite3.Row
        return db

    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)")
        db.commit()

    @app.get("/")
    def index():
        return jsonify(service="cloud-tasks-api", message="API de tarefas em nuvem", endpoints=["/health", "/tasks"])

    @app.get("/health")
    def health():
        try:
            with connect() as db:
                db.execute("SELECT 1").fetchone()
            return jsonify(status="ok"), 200
        except sqlite3.Error:
            return jsonify(status="error"), 503

    @app.get("/tasks")
    def list_tasks():
        with connect() as db:
            items = db.execute("SELECT id, title, done FROM tasks ORDER BY id").fetchall()
        return jsonify([dict(id=r["id"], title=r["title"], done=bool(r["done"])) for r in items])

    @app.post("/tasks")
    def create_task():
        data = request.get_json(silent=True)
        title, error = validate_title(data.get("title") if isinstance(data, dict) else None)
        if error:
            return jsonify(error=error), 400
        with connect() as db:
            cursor = db.execute("INSERT INTO tasks(title) VALUES (?)", (title,))
            db.commit()
            task_id = cursor.lastrowid
        return jsonify(id=task_id, title=title, done=False), 201

    @app.patch("/tasks/<int:task_id>")
    def update_task(task_id):
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not ("title" in data or "done" in data):
            return jsonify(error="informe title e/ou done"), 400
        fields = {}
        if "title" in data:
            title, error = validate_title(data["title"])
            if error:
                return jsonify(error=error), 400
            fields["title"] = title
        if "done" in data:
            if type(data["done"]) is not bool:
                return jsonify(error="done deve ser booleano"), 400
            fields["done"] = int(data["done"])
        assignments = ", ".join(f"{column}=?" for column in fields)
        with connect() as db:
            cursor = db.execute(f"UPDATE tasks SET {assignments} WHERE id=?", (*fields.values(), task_id))
            db.commit()
            if not cursor.rowcount:
                return jsonify(error="tarefa nao encontrada"), 404
            row = db.execute("SELECT id, title, done FROM tasks WHERE id=?", (task_id,)).fetchone()
        return jsonify(id=row["id"], title=row["title"], done=bool(row["done"])), 200

    @app.delete("/tasks/<int:task_id>")
    def delete_task(task_id):
        with connect() as db:
            cursor = db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            db.commit()
        if not cursor.rowcount:
            return jsonify(error="tarefa nao encontrada"), 404
        return "", 204

    return app


app = create_app()
