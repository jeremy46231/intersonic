import asyncio
import pathlib
from threading import Lock, Thread
from flask import Flask, render_template, request, jsonify

from download import download_missing
from metadata.main import process_directory
from tailscale import tailscale_setup

app = Flask(__name__, template_folder="templates", static_folder="static")

# Gunicorn must have a single worker process for this to work correctly
TASK_LOCK = Lock()

TASK_STATE = {"is_running": False, "message": "Idle. Ready to accept tasks."}


def update_status(message: str):
    """A thread-safe way to update the global status."""
    global TASK_STATE
    with TASK_LOCK:
        TASK_STATE["message"] = message
        print(f"Status Updated: {message}")


def run_download_task(queries: list[str]):
    """The wrapper function that will run in a separate thread."""
    global TASK_STATE

    # threads do not get a default event loop, so we create one for spotdl
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Pass our status_callback to the core download function
        download_missing(queries, status_callback=update_status)
        update_status("Idle. Download complete.")
    except Exception as e:
        print(f"An error occurred in download thread: {e}")
        update_status(f"Error during download: {e}")
    finally:
        with TASK_LOCK:
            TASK_STATE["is_running"] = False


def run_process_task():
    """Wrapper for the metadata processing task."""
    global TASK_STATE

    # threads do not get a default event loop, so we create one for spotdl
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        update_status("Processing metadata for all files...")
        process_directory(pathlib.Path("/music"))
        update_status("Idle. Metadata processing complete.")
    except Exception as e:
        print(f"An error occurred in process thread: {e}")
        update_status(f"Error during processing: {e}")
    finally:
        with TASK_LOCK:
            TASK_STATE["is_running"] = False


print("Initializing Tailscale...")
tailscale_setup()
print("Tailscale setup complete.")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start_task", methods=["POST"])
def start_task():
    """
    A single endpoint to start either task. It returns immediately
    and kicks off the background thread.
    """
    global TASK_STATE
    task_type = request.form.get("task_type")

    with TASK_LOCK:
        if TASK_STATE["is_running"]:
            return (
                render_template("_status.html", status="Task already in progress."),
                429,
            )

        TASK_STATE["is_running"] = True

        if task_type == "download":
            queries_text = request.form.get("queries", "")
            queries = [q.strip() for q in queries_text.splitlines() if q.strip()]
            if not queries:
                TASK_STATE["is_running"] = False
                return render_template(
                    "_status.html", status="Idle. No queries provided."
                )

            print(f"Received {len(queries)} queries for download.")

            TASK_STATE["message"] = f"Starting download for {len(queries)} queries..."
            thread = Thread(target=run_download_task, args=(queries,))
            thread.start()

        elif task_type == "process":
            print("Starting metadata processing task...")
            TASK_STATE["message"] = "Starting metadata processing..."
            thread = Thread(target=run_process_task)
            thread.start()

        else:
            TASK_STATE["is_running"] = False
            return render_template("_status.html", status="Invalid task type."), 400

    return render_template("_status.html", status=TASK_STATE["message"])


@app.route("/status")
def get_status():
    """The polling endpoint. Returns the current status."""
    global TASK_STATE
    with TASK_LOCK:
        return render_template("_status.html", status=TASK_STATE["message"])
