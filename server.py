"""
Flask Web Server + Orchestrator for Band Agents Hackathon.
Serves the demo web UI and orchestrates the multi-agent pipeline.
"""
import os
import sys
import json
import time
import logging
import threading
from typing import Dict, Optional

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
# Explicitly load from project root
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

from core.pipeline import AgentPipeline, PipelineResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SERVER] %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="web", static_url_path="")
CORS(app)

# Global state for tracking pipeline progress
active_tasks: Dict[str, dict] = {}


@app.route("/")
def index():
    """Serve the main demo UI."""
    return send_from_directory("web", "index.html")


@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "agents": {
            "architect": bool(os.getenv("BAND_ARCHITECT_ID")),
            "developer": bool(os.getenv("BAND_DEVELOPER_ID")),
            "reviewer": bool(os.getenv("BAND_REVIEWER_ID")),
            "qatest": bool(os.getenv("BAND_QATEST_ID")),
        },
        "llm_model": os.getenv("LLM_MODEL", "qwen3.7-plus"),
    })


@app.route("/api/diag")
def diag():
    """Diagnostic endpoint to check runtime environment."""
    import sys as _sys
    libs = {}
    for lib in ["httpx", "requests", "urllib3", "httpcore", "h11"]:
        try:
            mod = __import__(lib)
            libs[lib] = getattr(mod, "__version__", "?") + " | " + getattr(mod, "__file__", "?")
        except ImportError:
            libs[lib] = "NOT INSTALLED"
    return jsonify({
        "python": _sys.executable,
        "version": _sys.version,
        "cwd": os.getcwd(),
        "path": _sys.path[:8],
        "libraries": libs,
    })


@app.route("/api/generate", methods=["POST"])
def generate():
    """Start a new pipeline execution. Returns task_id immediately."""
    data = request.get_json()
    project_description = data.get("description", "").strip()

    if not project_description:
        return jsonify({"error": "Project description is required"}), 400

    if len(project_description) < 10:
        return jsonify({"error": "Project description too short (min 10 chars)"}), 400

    task_id = f"task_{int(time.time() * 1000)}"

    # Initialize task state
    active_tasks[task_id] = {
        "status": "started",
        "description": project_description,
        "progress": {},
        "result": None,
        "error": None,
    }

    # Run pipeline in background thread
    thread = threading.Thread(
        target=_run_pipeline,
        args=(task_id, project_description),
        daemon=True,
    )
    thread.start()

    return jsonify({"task_id": task_id, "status": "started"})


@app.route("/api/task/<task_id>")
def task_status(task_id):
    """Get the current status of a pipeline task."""
    task = active_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "error": task["error"],
        "has_result": task["result"] is not None,
    })


@app.route("/api/task/<task_id>/result")
def task_result(task_id):
    """Get the full result of a completed pipeline task."""
    task = active_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    if task["status"] != "completed":
        return jsonify({"error": "Task not yet completed", "status": task["status"]}), 400

    return jsonify(task["result"])


@app.route("/api/task/<task_id>/stream")
def task_stream(task_id):
    """SSE endpoint for real-time progress updates."""
    def generate():
        last_state = None
        max_retries = 600  # 10 minutes at 1s interval
        retries = 0

        while retries < max_retries:
            task = active_tasks.get(task_id)
            if not task:
                break

            current_state = {
                "status": task["status"],
                "progress": task["progress"],
                "error": task["error"],
            }

            # Only send if state changed
            state_json = json.dumps(current_state)
            if state_json != last_state:
                yield f"data: {state_json}\n\n"
                last_state = state_json

            if task["status"] in ("completed", "failed"):
                break

            time.sleep(1)
            retries += 1

        # Send final state
        task = active_tasks.get(task_id)
        if task:
            final_state = {
                "status": task["status"],
                "progress": task["progress"],
                "error": task["error"],
            }
            yield f"data: {json.dumps(final_state)}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _run_pipeline(task_id: str, description: str):
    """Run the multi-agent pipeline in background."""
    task = active_tasks.get(task_id)
    if not task:
        return

    def on_progress(agent_key: str, status: str, result):
        """Callback for pipeline progress."""
        task["progress"][agent_key] = {
            "status": status,
            "agent_name": agent_key.capitalize(),
        }
        if result and result.success:
            # Truncate output for progress display
            task["progress"][agent_key]["preview"] = result.output[:500] + "..."

    try:
        pipeline = AgentPipeline(on_progress=on_progress)
        result = pipeline.run(description)

        task["result"] = result.to_dict()
        task["status"] = "completed"
        logger.info(f"Task {task_id} completed in {result.total_time:.2f}s")

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        task["status"] = "failed"
        task["error"] = str(e)


def main():
    """Start the Flask server."""
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "3000"))

    logger.info("=" * 60)
    logger.info("Band Agents Hackathon - Server Starting")
    logger.info(f"  Address: http://{host}:{port}")
    logger.info(f"  LLM: {os.getenv('LLM_MODEL', 'qwen3.7-plus')}")
    logger.info(f"  Agents: Architect, Developer, Reviewer, QATest")
    logger.info("=" * 60)

    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
