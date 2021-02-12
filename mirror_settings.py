import json

WELCOME_MESSAGES = ["Welcome you look beautiful today!",
                    "How are you today?",
                    "I am glad to see you back!"]

KIVY_FONTS = [{
    "name": "Roboto-Mono",
    "fn_regular": "./assets/fonts/RobotoMono-Regular.ttf"
}]

default_json = {
    "Wit": {
        "api_key": "API_KEY"
    },
    "Speech": {
        "launch_phrase": "mirror mirror on the wall",
        "close_phrase": "thank you mirror"
    }
}

settings_json = json.dumps([
    {
        "type": "title",
        "title": "Wit.ai"
    },
    {
        "type": "string",
        "title": "API KEY",
        "desc": "The wit.ai API key",
        "section": "Wit",
        "key": "api_key"
    },
    {
        "type": "title",
        "title": "Speech"
    },
    {
        "type": "string",
        "title": "Launch Phrase",
        "desc": "Phrase to launch interaction with mirror",
        "section": "Speech",
        "key": "launch_phrase"
    },
    {
        "type": "string",
        "title": "Close Phrase",
        "desc": "Phrase to stop interaction with mirror",
        "section": "Speech",
        "key": "close_phrase"
    }
])
