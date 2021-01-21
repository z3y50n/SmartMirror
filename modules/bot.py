from configparser import ConfigParser
import os
import json

from wit import Wit


CONFIG_PATH = os.path.join(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir)), "smartmirror.ini")


class Bot():
    """A class for interacting with Wit.ai bot"""
    _api_token = ""
    _client = None

    def __init__(self) -> None:
        super().__init__()
        config = ConfigParser()
        config.read(CONFIG_PATH)
        self._api_token = config["Wit"]["api_key"]
        self._client = Wit(self._api_token)

    def message(self, text):
        try:
            resp = self._client.message(text)
            if resp['intents'] and resp['intents'][0]['confidence'] > 0.7:
                print(json.dumps(resp, indent=4))
                return resp
            print("Wit could not understand you")
            return
        except:
            print("Bad request")
            return


if __name__ == "__main__":
    Bot().message("hello world")
