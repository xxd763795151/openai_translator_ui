import os
import time

import openai
from openai import OpenAI

from openai_translator_ui.ai_translator.model import Model
from openai_translator_ui.ai_translator.utils import LOG


class OpenAIModel(Model):
    def __init__(self, model: str, api_key: str):
        self.model = model
        # 定义代理服务器地址和端口
        # proxy_url = "socks5://127.0.0.1:1081"
        # 设置环境变量，不在代码里设置了
        # os.environ["http_proxy"] = proxy_url
        # os.environ["https_proxy"] = proxy_url
        # 创建带有代理设置的Client实例
        # proxies = {"http": proxy_url, "https": proxy_url}
        # self.client = OpenAI(api_key=api_key, http_client=httpx.Client(proxies=proxies))
        # self.client = OpenAI(api_key=api_key, http_client=httpx.AsyncClient(proxies=proxies))
        self.client = OpenAI(api_key=api_key)

    def make_request(self, prompt):
        attempts = 0
        while attempts < 3:
            try:
                if self.model == "gpt-3.5-turbo":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    translation = response.choices[0].message.content.strip()
                else:
                    response = self.client.completions.create(
                        model=self.model,
                        prompt=prompt,
                        max_tokens=150,
                        temperature=0
                    )
                    translation = response.choices[0].text.strip()

                return translation, True
            except openai.RateLimitError as e:
                attempts += 1
                if attempts < 3:
                    LOG.warning("Rate limit reached. Waiting for 60 seconds before retrying.")
                    time.sleep(60)
                else:
                    raise Exception("Rate limit reached. Maximum attempts exceeded.")
            except openai.APIConnectionError as e:
                print("The server could not be reached")
                print(
                    e.__cause__)  # an underlying Exception, likely raised within httpx.            except requests.exceptions.Timeout as e:
            except openai.APIStatusError as e:
                print("Another non-200-range status code was received")
                print(e.status_code)
                print(e.response)
                return F'{e.status_code}: {e.response}', False
            except Exception as e:
                raise Exception(f"发生了未知错误：{e}")
        return "", False
