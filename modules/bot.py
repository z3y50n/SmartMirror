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
                return self.format_response(resp)
                
            print("Wit could not understand you")
            return
        except Exception as e: 
            print(e)
            print("Bad request")
            return

    def format_response(self, resp):
        intent = resp['intents'][0]['name']
        args = {entity[0]['name'] if not entity[0]['name'].startswith("wit$") else entity[0]['name'][4:]: entity[0]['value']
                for entity in resp['entities'].values()}
        return {"intent": intent, "args": args}

    # def format_response(self, resp):
    #     intent = resp['intents'][0]['name'].split("_", 1)
    #     widget_name = intent[0]
    #     function_name = intent[1]
    #     args = {entity[0]['name'] if not entity[0]['name'].startswith("wit$") else entity[0]['name'][4:]: entity[0]['value']
    #             for entity in resp['entities'].values()}


    #     return {"widget": widget_name, "function": function_name, "args": args}


if __name__ == "__main__":
    Bot().message("hello world")
