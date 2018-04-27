#

import unittest

from mra.http_pool import HTTPPool

from base_test import BaseTest

class ResourcePoolTest(BaseTest):
    def test_put(self):
        async def test():
            with await HTTPPool().acquire() as pool:
                cookies = await pool.get("http://httpbin.org/cookies")
                print(await cookies.json())
                await pool.get("http://httpbin.org/cookies/set?name=value")
                cookies = await pool.get("http://httpbin.org/cookies")
                print(await cookies.json())
                cookies = await pool.get("http://httpbin.org/cookies", headers={'test': 'header'})
                print(await cookies.json())
                # PUT  id = 17515 terminal:=@test.json
                # "Cookie: "
                cookies = await pool.put("http://httpbin.org/put", headers={'test': 'header'}, json={'test':'body'})
                print(await cookies.json())
                headers = {
                    "Cookie": '_terminal_provisioning_session=VkpmWGhZenBXT1BId0MrVWh4eEtIVWNkSHBuNnc0N1BWTHJwWXVhelZKUy95VXhabDdGdmg5Y3RxSUdvMHRmd1huTWhpNGsxa1NjZXR3YUl5TzdEYWNIanRnMElVcHY1c1djeFdDejhiQlZRVVBIeXkrV3p1emhFV1JpSU5GdmVtamZTd0l0aXhNQTJkS3NhaXVaM3Q0QStrWVlvSDRuUkpaU2gyNGZwejE3QStkVnNrOFFKYVpGNEdtKzBKakN4akVodTBMU0pjbmdjb0NXYTZoWXVtYXJ4ZnFnSzU4d21Ud2V6WFRaUWEzT3gwWTJkanZUdTNMbFJhR21PYm1sRGd5VFFnNjhWQ2p4WXVuYWJmamUxZlBJSUtiSE5RZUw5RXZGRXlCNTlpeERmcjg4RDkvUjdaYUUvTlhXREw2OWsvWGs0bjlVdDdVYnllU0ZVRG9HdDlnPT0tLWZhNDZtdHZoQkxvR0Y0ZHBKUXNlaVE9PQ%3D%3D--dc18b103ed15a4ed21f8cee09af651a267bd39c1',
                    "X-CSRF-Token": "FBTm7Ck1OoIUxZGC3fJY1gBBie/eGdE0qdlMNJio8P5akT+N+bAqy5fmHOq2UEXzoHY/hrBobZORAIM8O/thWw=="
                }
                jsn = {
                    "id": 171515,
                    "terminal": {
                        'check_in_timeout': 86400,
                        'customer_serial_number': None,
                        'estate_id': 49,
                        'idle_text': None,
                        'name': 'Demo Terminal 1',
                        'nfc_behavior': 'inherit',
                        'organization_id': 1408,
                        'remove_image': False,
                        'serial_number': '17240PP83351394',
                        'source_ids': [4329],
                        'terminal_model_id': 5,
                        'timeout': 300,
                        'validated_p2pe': 'inherit'
                    }
                }
                cookies = await pool.put("https://tap.paymentfusion.com/terminals/17515.json", json=jsn, headers=headers)
                print(cookies)
                print(await cookies.text())
                # print(await cookies.json())


        self.async_test(test)

if __name__ == '__main__':
    unittest.main()