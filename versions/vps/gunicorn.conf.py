#!/usr/bin/env python3
"""
Gunicorn configuration for VPS deployment
"""
import os
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = int(os.environ.get('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = os.environ.get('WORKER_CLASS', 'sync')
worker_connections = 1000
timeout = int(os.environ.get('WORKER_TIMEOUT', 300))
keepalive = 5
max_requests = int(os.environ.get('MAX_REQUESTS', 1000))
max_requests_jitter = int(os.environ.get('MAX_REQUESTS_JITTER', 100))

# Restart workers after this many requests
preload_app = True

# Logging
accesslog = '/app/logs/access.log'
errorlog = '/app/logs/error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'consolidador_pedidos'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None
tmp_upload_dir = '/app/temp'

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)