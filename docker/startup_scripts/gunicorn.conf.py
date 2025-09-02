# /var/interlegis/sapl/gunicorn.conf.py

import os
import pathlib
import multiprocessing

# ---- SAPL app configuration ----
NAME = "SAPL"
DJANGODIR = "/var/interlegis/sapl"
SOCKFILE = f"unix:{DJANGODIR}/run/gunicorn.sock"
USER = "sapl"
GROUP = "nginx"
NUM_WORKERS = int(os.getenv("WEB_CONCURRENCY", "3"))
THREADS = int(os.getenv("GUNICORN_THREADS", "8"))
TIMEOUT = int(os.getenv("GUNICORN_TIMEOUT", "300"))
MAX_REQUESTS = 1000
WORKER_CLASS = "gthread"
DJANGO_SETTINGS = "sapl.settings"
WSGI_APP = "sapl.wsgi:application"

# ---- gunicorn settings ----
# Equivalent of: --name
proc_name = NAME

# Equivalent of: --bind=unix:...
# For quick testing via browser, you can switch to: bind = "0.0.0.0:8000"
bind = f"unix:{SOCKFILE}"
umask = 0o007
user = USER
group = GROUP

# Ensure imports work like in your script’s working dir
chdir = DJANGODIR

# Allow starting with just: gunicorn -c gunicorn.conf.py
wsgi_app = WSGI_APP

# Logs
loglevel = "debug"
accesslog = "/var/log/sapl/access.log"
errorlog = "/var/log/sapl/error.log"
# errorlog = "-"          # send to stderr (so you see it in docker logs or terminal)
# accesslog = "-"         # send to stdout
capture_output = True  # capture print/tracebacks from app

# Worker/process lifecycle
workers = NUM_WORKERS
worker_class = WORKER_CLASS
threads = THREADS
timeout = TIMEOUT
graceful_timeout = 30
keepalive = 10
backlog = 2048
max_requests = MAX_REQUESTS
max_requests_jitter = 100

# Environment (same as exporting before running)
raw_env = [
    f"DJANGO_SETTINGS_MODULE={DJANGO_SETTINGS}",
    # If you’re using ReportLab and seeing segfaults with PDFs, keep this:
    # "RL_NOACCEL=1",
]

# If you previously enabled preload and saw segfaults with native libs, keep it off:
preload_app = False


# Create the run/ directory for the UNIX socket (your script did this)
def on_starting(server):
    pathlib.Path(SOCKFILE).parent.mkdir(parents=True, exist_ok=True)


# Close DB connections after fork (safer when using preload or certain DB drivers)
def post_fork(server, worker):
    try:
        from django import db

        db.connections.close_all()
    except Exception:
        # Django not initialized yet or not available
        pass
