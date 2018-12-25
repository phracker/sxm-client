from .synchronous import make_sync_http_handler, run_sync_http_server  # noqa

# async http server requires aiohttp to be installed
try:
    from .asynchronous import make_async_http_app, run_async_http_server  # noqa
except ImportError:
    __all__ = [
        'make_sync_http_handler', 'run_sync_http_server',
    ]
else:
    __all__ = [
        'make_sync_http_handler', 'run_sync_http_server',
        'make_async_http_app', 'run_async_http_server',
    ]
