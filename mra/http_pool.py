import aiohttp
from resource_pool import ResourcePool

class 

class HTTPPool(ResourcePool):
    MAX_ALLOCATION = 10
    COOKIE_JAR = None

    # methods
    _POST = "POST"
    _GET = "GET"
    _POST_JSON = "POST_JSON"

    @classmethod
    def _create_global_values(cls):
        cls.COOKIE_JAR = aiohttp.CookieJar()

    @classmethod
    def _create_resource(cls):
        return aiohttp.ClientSession(cookie_jar=cls.COOKIE_JAR)

    async def get(self, url, params=None, headers=None):
        return await self._request(self._GET, 
            params=params)

    async def post(self, url, params=None, body=None, headers=None):
        return await self._request(self._POST, 
            params, body)

    async def post_json(self, url, params=None, body=None, headers=None):
        return await self._request(self._POST_JSON, 
            params, body)

    async def _request(self, method, params=None, body=None, headers=None):

        if params == None:
            params = {}

        if headers == None:
            headers = {}

        if type(params) is not dict:
            raise TypeError("Params must be a dict!")

        result = None
        if (method == self._GET):
            result = await self._resource.get(url, params=params)
        if (method == self._POST):
            result = await self._resource.post(url, params=params, body=body)
        if (method == self._POST_JSON):
            headers['Content-Type'] = "application/json"
            if type(body) is not dict:
                raise TypeError("When sending JSON the body must be a dictionary!")
            result = await self.resource.post(url, params=params, json=body)

        return result
