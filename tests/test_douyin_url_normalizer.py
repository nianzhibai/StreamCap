import unittest
from unittest.mock import patch

import httpx

from app.utils.douyin_url_normalizer import (
    DouyinNormalizationError,
    looks_like_douyin_input,
    normalize_douyin_input,
)


class NormalizeDouyinInputTests(unittest.IsolatedAsyncioTestCase):
    def test_detects_douyin_share_text(self):
        self.assertTrue(
            looks_like_douyin_input(
                "复制下方链接，打开【抖音】，直接观看直播！ https://v.douyin.com/fBjnc1ZLEEY/"
            )
        )

    def test_detects_direct_douyin_live_room_url(self):
        self.assertTrue(looks_like_douyin_input("https://live.douyin.com/845632139263"))

    def test_returns_false_for_non_douyin_url(self):
        self.assertFalse(looks_like_douyin_input("https://www.huya.com/12345"))

    async def test_returns_live_room_url_unchanged(self):
        result = await normalize_douyin_input("https://live.douyin.com/845632139263")

        self.assertEqual(result, "https://live.douyin.com/845632139263")

    async def test_returns_live_room_url_with_douyin_id_unchanged(self):
        result = await normalize_douyin_input("https://live.douyin.com/yall1102")

        self.assertEqual(result, "https://live.douyin.com/yall1102")

    @patch("app.utils.douyin_url_normalizer.httpx.AsyncClient")
    async def test_resolves_share_text_with_short_link_to_live_room_url(self, client_cls):
        client = client_cls.return_value.__aenter__.return_value
        client.get.return_value = httpx.Response(
            200,
            request=httpx.Request("GET", "https://v.douyin.com/fBjnc1ZLEEY/"),
            text='{"app":{"initialState":{"roomStore":{"roomInfo":{"room":{"webRid":"845632139263"}}}}}',
        )

        result = await normalize_douyin_input(
            (
                "8- #在抖音，记录美好生活#【浪羽pubg】正在直播，"
                "来和我一起支持Ta吧。复制下方链接，打开【抖音】，直接观看直播！ "
                "https://v.douyin.com/fBjnc1ZLEEY/ 2@2.com :8pm"
            )
        )

        self.assertEqual(result, "https://live.douyin.com/845632139263")

    @patch("app.utils.douyin_url_normalizer.httpx.AsyncClient")
    async def test_resolves_raw_short_link_to_live_room_url(self, client_cls):
        client = client_cls.return_value.__aenter__.return_value
        client.get.return_value = httpx.Response(
            200,
            request=httpx.Request("GET", "https://v.douyin.com/example/"),
            text='{"webRid":"845632139263"}',
        )

        result = await normalize_douyin_input("https://v.douyin.com/example/")

        self.assertEqual(result, "https://live.douyin.com/845632139263")

    @patch("app.utils.douyin_url_normalizer.httpx.AsyncClient")
    async def test_resolves_short_link_to_live_room_url_from_escaped_web_rid(self, client_cls):
        client = client_cls.return_value.__aenter__.return_value
        client.get.return_value = httpx.Response(
            200,
            request=httpx.Request("GET", "https://v.douyin.com/example/"),
            text='... \\"webRid\\":\\"935126084727\\" ...',
        )

        result = await normalize_douyin_input("https://v.douyin.com/example/")

        self.assertEqual(result, "https://live.douyin.com/935126084727")

    @patch("app.utils.douyin_url_normalizer.httpx.AsyncClient")
    async def test_resolves_short_link_from_final_redirected_response_url_without_web_rid(self, client_cls):
        client = client_cls.return_value.__aenter__.return_value
        client.get.return_value = httpx.Response(
            200,
            request=httpx.Request("GET", "https://live.douyin.com/845632139263"),
            text="<html></html>",
        )

        result = await normalize_douyin_input("https://v.douyin.com/example/")

        self.assertEqual(result, "https://live.douyin.com/845632139263")

    @patch("app.utils.douyin_url_normalizer.httpx.AsyncClient")
    async def test_raises_when_response_does_not_contain_web_rid(self, client_cls):
        client = client_cls.return_value.__aenter__.return_value
        client.get.return_value = httpx.Response(
            200,
            request=httpx.Request("GET", "https://v.douyin.com/example/"),
            text="<html></html>",
        )

        with self.assertRaises(DouyinNormalizationError):
            await normalize_douyin_input("https://v.douyin.com/example/")

    @patch("app.utils.douyin_url_normalizer.httpx.AsyncClient")
    async def test_raises_on_http_or_network_errors(self, client_cls):
        client = client_cls.return_value.__aenter__.return_value
        client.get.side_effect = httpx.HTTPError("network down")

        with self.assertRaises(DouyinNormalizationError):
            await normalize_douyin_input("https://v.douyin.com/example/")

    @patch("app.utils.douyin_url_normalizer.httpx.AsyncClient")
    async def test_raises_on_non_2xx_http_response(self, client_cls):
        client = client_cls.return_value.__aenter__.return_value
        client.get.return_value = httpx.Response(
            404,
            request=httpx.Request("GET", "https://v.douyin.com/example/"),
            text="not found",
        )

        with self.assertRaises(DouyinNormalizationError):
            await normalize_douyin_input("https://v.douyin.com/example/")


if __name__ == "__main__":
    unittest.main()
