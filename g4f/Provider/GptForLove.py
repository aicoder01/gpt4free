from __future__ import annotations

from aiohttp import ClientSession
import execjs, os, json

from ..typing import AsyncGenerator
from .base_provider import AsyncGeneratorProvider
from .helper import format_prompt

class GptForLove(AsyncGeneratorProvider):
    url = "https://ai18.gptforlove.com"
    supports_gpt_35_turbo = True
    working = True

    @classmethod
    async def create_async_generator(
        cls,
        model: str,
        messages: list[dict[str, str]],
        **kwargs
    ) -> AsyncGenerator:
        if not model:
            model = "gpt-3.5-turbo"
        headers = {
            "authority": "api.gptplus.one",
            "accept": "application/json, text/plain, */*",
            "accept-language": "de-DE,de;q=0.9,en-DE;q=0.8,en;q=0.7,en-US;q=0.6,nl;q=0.5,zh-CN;q=0.4,zh-TW;q=0.3,zh;q=0.2",
            "content-type": "application/json",
            "origin": cls.url,
            "referer": f"{cls.url}/",
            "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Linux",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        }
        async with ClientSession(headers=headers) as session:
            prompt = format_prompt(messages)
            data = {
                "prompt": prompt,
                "options": {},
                "systemMessage": "You are ChatGPT, the version is GPT3.5, a large language model trained by OpenAI. Follow the user's instructions carefully. Respond using markdown.",
                "temperature": 0.8,
                "top_p": 1,
                "secret": get_secret(),
                **kwargs
            }
            async with session.post("https://api.gptplus.one/chat-process", json=data) as response:
                response.raise_for_status()
                async for line in response.content:
                    line = json.loads(line)
                    if "detail" in line:
                        content = line["detail"]["choices"][0]["delta"].get("content")
                        if content:
                            yield content
                    elif "10分钟内提问超过了5次" in line:
                        raise RuntimeError("Rate limit reached")
                    else:
                        raise RuntimeError(f"Response: {line}")


def get_secret() -> str:
    dir = os.path.dirname(__file__)
    dir += '/npm/node_modules/crypto-js'
    source = """
CryptoJS = require('{dir}/crypto-js')
var k = '14487141bvirvvG'
    , e = Math.floor(new Date().getTime() / 1e3);
var t = CryptoJS.enc.Utf8.parse(e)
    , o = CryptoJS.AES.encrypt(t, k, {
    mode: CryptoJS.mode.ECB,
    padding: CryptoJS.pad.Pkcs7
});
return o.toString()
"""
    source = source.replace('{dir}', dir)
    return execjs.compile(source).call('')
