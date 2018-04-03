from aiohttp import web
import json

async def echo(request):
    """

    :param aiohttp.web_reqrep.Request request:
    :return:
    """

    headers = ["Accept", "Accept-Encoding", "Connection", "Host", "User-Agent", "Content-Length"]


    result = {
        "method": request.method,
        "path": request.path.strip("/").split("/"),
        "query": request.query_string,
        "content-type": request.content_type,
        # fix me
        #"date": time. (""time.localtime(time.time()))
    }

    # headers
    header_dict = dict(request.headers)
    for header in headers:
        result[header] = header_dict[header]
        del header_dict[header]

    result["extra headers"] = header_dict

    if request.method == 'POST':
        data = await request.text()
        if result['content-type'] == "application/json":
            data = json.loads(data)

        result['body'] = data

    return web.json_response(result)

def setup_routes(app):
    # dumb but effective
    path = ''
    for part in ['a', 'b', 'c', 'd', 'e', 'f']:
        path += "/{" + part + "}"
        app.router.add_get(path, echo)
        app.router.add_post(path, echo)

app = web.Application()
setup_routes(app)
web.run_app(app, host='127.0.0.1', port=5000)