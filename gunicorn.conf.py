worker_class = "uvicorn.workers.UvicornWorker"
bind = "unix:botko.sock"
workers = 1
threads = 4
proc_name = "botko"
pidfile = "/var/run/gunicorn-botko.pid"
