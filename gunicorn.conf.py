proc_name = "botko"
bind = "unix:botko.sock"
workers = 1
threads = 4
worker_class = "uvicorn.workers.UvicornWorker"
