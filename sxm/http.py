"""HTTP Server module for sxm"""
import json
import logging
from asyncio import get_event_loop, sleep
from typing import Any, Callable, Coroutine, Dict, List

from aiohttp import web

from sxm.client import HLS_AES_KEY, SegmentRetrievalException, SXMClient, SXMClientAsync

__all__ = ["make_http_handler", "run_http_server"]


def make_http_handler(
    sxm: SXMClientAsync, cache_aac_chunks: bool = True
) -> Callable[[web.Request], Coroutine[Any, Any, web.Response]]:
    """
    Creates and returns a configured `aiohttp` request handler ready to be used
    by a :meth:`aiohttp.web.run_app` instance with your :class:`SXMClient`.

    Really useful if you want to create your own HTTP server as part
    of another application.

    Parameters
    ----------
    sxm : :class:`SXMClient`
        SXM client to use
    """

    aac_cache: Dict[str, bytes] = {}

    async def get_segment(path: str):
        try:
            data = await sxm.get_segment(path)
        except SegmentRetrievalException:
            await sxm.close_session()
            sxm.reset_session()
            await sxm.authenticate()
            data = await sxm.get_segment(path)

        return data

    async def cache_playlist(playlist: List[str]):
        for item in playlist:
            while len(aac_cache) > 10:
                await sleep(1)

            if not item.startswith("AAC_Data"):
                continue

            data = await get_segment(item)
            if data is not None:
                aac_cache[item] = data
            await sleep(1)

    async def sxm_handler(request: web.Request):
        """SXM Response handler"""

        response = web.Response(status=404)
        if request.path.endswith(".m3u8"):
            if not sxm.primary:
                sxm.set_primary(True)
            playlist = await sxm.get_playlist(request.path.rsplit("/", 1)[1][:-5])

            if playlist:
                if cache_aac_chunks:
                    loop = get_event_loop()
                    loop.create_task(cache_playlist(playlist.split("\n")))
                response = web.Response(
                    status=200,
                    body=bytes(playlist, "utf-8"),
                    headers={"Content-Type": "application/x-mpegURL"},
                )
            else:
                response = web.Response(status=503)
        elif request.path.endswith(".aac"):
            segment_path = request.path[1:]
            if segment_path in aac_cache:
                data = aac_cache[segment_path]
                del aac_cache[segment_path]
            else:
                data = await get_segment(segment_path)

            if data:
                response = web.Response(
                    status=200,
                    body=data,
                    headers={"Content-Type": "audio/x-aac"},
                )
            else:
                response = web.Response(status=503)
        elif request.path.endswith("/key/1"):
            response = web.Response(
                status=200,
                body=HLS_AES_KEY,
                headers={"Content-Type": "text/plain"},
            )
        elif request.path.endswith("/channels/"):
            try:
                raw_channels = await sxm.get_channels()
            except Exception:
                raw_channels = []

            if len(raw_channels) > 0:
                response = web.Response(
                    status=200,
                    body=json.dumps(raw_channels).encode("utf-8"),
                    headers={"Content-Type": "application/json; charset=utf-8"},
                )
            else:
                response = web.Response(status=403)

        return response

    return sxm_handler


def run_http_server(
    sxm: SXMClient,
    port: int,
    ip="0.0.0.0",  # nosec
    logger: logging.Logger = None,
    cache_aac_chunks: bool = True,
) -> None:
    """
    Creates and runs an instance of :class:`http.server.HTTPServer` to proxy
    SXM requests without authentication.

    You still need a valid SXM account with streaming rights,
    via the :class:`SXMClient`.

    Parameters
    ----------
    port : :class:`int`
        Port number to bind SXM Proxy server on
    ip : :class:`str`
        IP address to bind SXM Proxy server on
    """

    if logger is None:
        logger = logging.getLogger(__file__)

    if not sxm.authenticate():
        logging.fatal("Could not log into SXM")
        exit(1)

    if not sxm.configuration:
        logging.fatal("Could not get SXM configuration")
        exit(1)

    app = web.Application()
    app.router.add_get("/{_:.*}", make_http_handler(sxm.async_client))
    try:
        logger.info(f"running SXM proxy server on http://{ip}:{port}")
        web.run_app(
            app,
            host=ip,
            port=port,
            access_log=logger,
            print=None,  # type: ignore
        )
    except KeyboardInterrupt:
        pass
