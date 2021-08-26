from configparser import ConfigParser
import os
import json

from wit import Wit

from modules.basedir import BASEDIR

CONFIG_PATH = os.path.join(BASEDIR, "smartmirror.ini")


class Bot:
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
            if resp["intents"] and resp["intents"][0]["confidence"] > 0.7:
                print(json.dumps(resp, indent=4))
                return self.format_response(resp)

            print("Wit could not understand you")
            return
        except Exception as e:
            print(e)
            print("Bad request")
            return

    def format_response(self, resp):
        intent = resp["intents"][0]["name"]
        if intent == "request_location":
            args = {
                "location": resp["entities"]["wit$location:location"][0]["resolved"][
                    "values"
                ][0]["name"]
            }
        else:
            args = {
                entity[0]["name"].split(":", 1)[0]
                if not entity[0]["name"].startswith("wit$")
                else entity[0]["name"][4:]: entity[0]["value"]
                for entity in resp["entities"].values()
            }
        return {"intent": intent, "args": args}


if __name__ == "__main__":
    Bot().message("hello world")
