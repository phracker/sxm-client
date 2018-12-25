from aiohttp import web

from ..client import HLS_AES_KEY


def make_async_http_app(sxm):
    async def playlist_handler(request):
        channel_id = request.match_info.get('channel_id', None)

        if sxm.get_channel(channel_id) is None:
            raise web.HTTPNotFound()

        data = sxm.get_playlist(channel_id)
        if data:
            response = web.StreamResponse(headers={
                'Content-Type': 'application/x-mpegURL'
            })
            await response.prepare(request)
            await response.write(bytes(data, 'utf-8'))
            await response.write_eof()
            return response
        else:
            raise web.HTTPBadRequest()

    async def aac_handler(request):
        channel_id = request.match_info.get('channel_id', None)
        arg_1 = request.match_info.get('arg_1', None)
        arg_2 = request.match_info.get('arg_2', None)

        if sxm.get_channel(channel_id) is None:
            raise web.HTTPNotFound()

        data = sxm.get_segment(
            f'/AAC_Data/{channel_id}/{arg_1}/{arg_2}.aac')
        if data:
            response = web.StreamResponse(headers={
                'Content-Type': 'audio/x-aac'
            })
            await response.prepare(request)
            await response.write(data)
            await response.write_eof()
            return response
        else:
            raise web.HTTPBadRequest()

    async def key_handler(request):
        response = web.StreamResponse(headers={
            'Content-Type': 'text/plain'
        })
        await response.prepare(request)
        await response.write(HLS_AES_KEY)
        await response.write_eof()
        return response

    app = web.Application()
    app.router.add_get('/{channel_id}.m3u8', playlist_handler)
    app.router.add_get('/AAC_Data/{channel_id}/{arg_1}/{arg_2}.aac', aac_handler)
    app.router.add_get('/key/1', key_handler)

    return app


def run_async_http_server(port, sxm):
    app = make_async_http_app(sxm)

    web.run_app(app, port=port)
