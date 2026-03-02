from datetime import datetime
import json
import os
import socket
from uuid import uuid4
from urllib import error as urllib_error
from urllib import request as urllib_request

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Corebot integration config
COREBOT_URL = os.getenv("COREBOT_URL", "http://localhost:8000").rstrip("/")
COREBOT_API_KEY = os.getenv("COREBOT_API_KEY", "")
COREBOT_TIMEOUT_SEC = int(os.getenv("COREBOT_TIMEOUT_SEC", "120"))
APP_VERSION = os.getenv("APP_VERSION", "todo-app-1.0.0")
DIAGNOSTICS_TOKEN = os.getenv("WEBAPP_DIAGNOSTICS_TOKEN", "")

# SQLAlchemy 2.0 style base class
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Todo Model
class Todo(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    description: Mapped[str] = mapped_column(db.String(500), nullable=True)
    complete: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self):
        return f'<Todo {self.title}>'

# Routes
@app.route('/')
def index():
    incomplete = db.session.query(Todo).filter_by(complete=False).all()
    complete = db.session.query(Todo).filter_by(complete=True).all()
    return render_template('index.html', incomplete=incomplete, complete=complete)

@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title')
    description = request.form.get('description', '')
    
    if title:
        new_todo = Todo(title=title, description=description, complete=False)
        db.session.add(new_todo)
        db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/complete/<int:id>')
def complete(id):
    todo = db.session.get(Todo, id)
    if todo:
        todo.complete = True
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    todo = db.session.get(Todo, id)
    if todo:
        db.session.delete(todo)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    todo = db.session.get(Todo, id)
    if todo:
        todo.title = request.form.get('title', todo.title)
        todo.description = request.form.get('description', todo.description)
        db.session.commit()
    return redirect(url_for('index'))

# API endpoints (optional REST API)
@app.route('/api/todos', methods=['GET'])
def api_get_todos():
    todos = db.session.query(Todo).all()
    return jsonify([{
        'id': todo.id,
        'title': todo.title,
        'description': todo.description,
        'complete': todo.complete,
        'created_at': todo.created_at.isoformat()
    } for todo in todos])


def _corebot_headers() -> dict[str, str]:
    """Build headers for Corebot API calls."""
    headers = {"Content-Type": "application/json"}
    if COREBOT_API_KEY.strip():
        headers["X-API-Key"] = COREBOT_API_KEY
    return headers


def _call_corebot_chat(payload: dict) -> tuple[dict, int]:
    """Call Corebot /chat endpoint and return JSON + status."""
    req = urllib_request.Request(
        url=f"{COREBOT_URL}/chat/",
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers=_corebot_headers(),
    )
    try:
        with urllib_request.urlopen(req, timeout=COREBOT_TIMEOUT_SEC) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body, int(resp.status)
    except urllib_error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="ignore")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"detail": raw or "Corebot request failed."}
        return parsed, int(exc.code)
    except urllib_error.URLError as exc:
        return {"detail": f"Corebot unreachable: {exc.reason}"}, 503
    except TimeoutError:
        return {"detail": "Corebot request timed out."}, 504
    except socket.timeout:
        return {"detail": "Corebot request timed out."}, 504
    except Exception as exc:
        return {"detail": f"Unexpected integration error: {exc}"}, 500


@app.route('/assistant/chat', methods=['POST'])
def assistant_chat():
    """Proxy chat requests from web UI to Corebot."""
    try:
        body = request.get_json(silent=True) or {}
        message = str(body.get("message", "")).strip()
        if not message:
            return jsonify({"detail": "message is required"}), 400

        history = body.get("history", [])
        if not isinstance(history, list):
            history = []

        mode = str(body.get("mode", "auto")).strip().lower()
        if mode not in {"auto", "info", "incident"}:
            mode = "auto"

        app_context = body.get("app_context", {})
        if not isinstance(app_context, dict):
            app_context = {}

        app_context.setdefault("app_name", "todo-app")
        app_context.setdefault("app_version", APP_VERSION)
        app_context.setdefault("session_id", request.cookies.get("session", "web-session"))
        app_context.setdefault("trace_id", request.headers.get("X-Trace-Id", str(uuid4())))

        payload = {
            "message": message,
            "history": history,
            "mode": mode,
            "app_context": app_context,
        }
        data, status = _call_corebot_chat(payload)
        return jsonify(data), status
    except Exception as exc:
        return jsonify({"detail": f"assistant_chat failed: {exc}"}), 500


@app.route('/support/context', methods=['GET'])
def support_context():
    """Provide diagnostics payload for Corebot incident mode tools."""
    if DIAGNOSTICS_TOKEN:
        auth = request.headers.get("Authorization", "")
        expected = f"Bearer {DIAGNOSTICS_TOKEN}"
        if auth != expected:
            return jsonify({"detail": "Unauthorized"}), 401

    trace_id = request.args.get("trace_id")
    session_id = request.args.get("session_id")

    try:
        total = db.session.query(Todo).count()
        completed = db.session.query(Todo).filter_by(complete=True).count()
        incomplete = db.session.query(Todo).filter_by(complete=False).count()
        diagnostics = {
            "status": "ok",
            "trace_id": trace_id,
            "session_id": session_id,
            "checks": [
                {"name": "db_connection", "status": "ok"},
                {"name": "todo_total", "status": "ok", "value": total},
                {"name": "todo_completed", "status": "ok", "value": completed},
                {"name": "todo_incomplete", "status": "ok", "value": incomplete},
            ],
        }
    except Exception as exc:
        diagnostics = {
            "status": "error",
            "trace_id": trace_id,
            "session_id": session_id,
            "checks": [{"name": "db_connection", "status": "error"}],
            "error": str(exc),
        }

    return jsonify(diagnostics)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0")
