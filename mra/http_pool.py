import aiohttp
import pprint

from urllib.parse import urlencode

from mra.resource_pool import ResourcePool

class HTTPPool(ResourcePool):
    PATH = "Resource.HTTPPool"
    MAX_ALLOCATION = 10
    COOKIE_JAR = None

    # methods
    _POST = "POST"
    _PUT = "PUT"
    _GET = "GET"
    _POST_JSON = "POST_JSON"

    def __init__(self):
        super().__init__()
        self._print_request = False

    @classmethod
    async def _create_global_values(cls):
        cls.COOKIE_JAR = aiohttp.CookieJar()

    @classmethod
    async def _create_resource(cls):
        return aiohttp.ClientSession(cookie_jar=cls.COOKIE_JAR, connector=aiohttp.TCPConnector(verify_ssl=False))

    def start_print(self):
        self._print_request = True

    def stop_print(self):
        self._print_request = False

    async def get(self, url, params=None, headers=None) -> aiohttp.ClientResponse:
        return await self._request(self._GET, url,
            params=params, headers=headers)

    async def post(self, url, params=None, body=None, json=None, headers=None) -> aiohttp.ClientResponse:
        return await self._request(self._POST, url,
            params, body=body, json=json, headers=headers)

    async def put(self, url, params=None, body=None, json=None, headers=None) -> aiohttp.ClientResponse:
        return await self._request(self._PUT, url,
            params, body=body, json=json, headers=headers)

    async def _request_string(self, method, url, params, body, json, headers):
        methods = {
            self._PUT: "PUT",
            self._GET: "GET",
            self._POST: "POST"
        }
        maybe_question = ''
        param_string = ''
        if params:
            maybe_question = '?'
            param_string = urlencode(params)

        lines = [
            "{method} {url}{maybe_question}{params}".format(
                method = methods[method],
                url = url,
                maybe_question = maybe_question,
                params = param_string
            )]

        cookies = self._resource.cookie_jar.filter_cookies(url)
        if cookies:
            headers['Cookie'] = cookies.output(header='')

        if headers:
            lines.append("{headers}".format(
                headers = '\n'.join(['{}: {}'.format(key, value) for key, value in headers.items()])
            ))
        if body is not None or json is not None:
            if body:
                lines.append("{body}".format(body = body))
            else:
                lines.append("{body}".format(body=pprint.pformat(json)))

        return  '------------\n{}\n------------'.format('\n\n'.join(lines))


    async def _request(self, method, url, params=None, body=None, json=None, headers=None) -> aiohttp.ClientResponse:

        if params == None:
            params = {}

        if headers == None:
            headers = {}

        if json is not None and body is not None:
            raise Exception("Can't do both body and json")

        if json is not None:
            headers['Content-Type'] = "application/json"
            if type(json) is not dict:
                raise TypeError("When sending JSON the body must be a dictionary!")

        if type(params) is not dict:
            raise TypeError("Params must be a dict!")

        log_str = await self._request_string(method, url, params, body, json, headers)
        if self._print_request:
            print(log_str)
        result = None
        if (method == self._GET):
            result = await self._resource.get(url, params=params, headers=headers)
        if (method == self._POST):
            result = await self._resource.post(url, params=params, data=body, json=json, headers=headers)
        if (method == self._PUT):
            print(f'PUT {url} headers:{headers }')
            result = await self._resource.put(url, params=params, data=body, json=json, headers=headers)

        return result
