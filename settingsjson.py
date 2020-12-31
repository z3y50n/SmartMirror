import json

settings_json = json.dumps([
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
    },
    {
        "type": "title",
        "title": "Weather"
    },
    {
        "type": "string",
        "title": "API KEY",
        "desc": "Openweathermap API key",
        "section": "WeatherAPI",
        "key": "api_key"
    },
    {
        "type": "string",
        "title": "City Id",
        "desc": "Openweathermap City's id",
        "section": "WeatherAPI",
        "key": "city_id"
    },
    {
        "type": "numeric",
        "title": "Update Interval",
        "desc": "How often to update the weather in seconds",
        "section": "WeatherAPI",
        "key": "update_interval"
    }
])


# {
#     "launch_phrase": "mirror mirror on the wall",
#     "close_phrase": "thank you mirror",
#     "WEATHER_API":{
#         "api_key": "26be86d9cd70b50cb932ddf568ebac0c",
#         "city_id": "8133841",
#         "update_interval": 1800
#     }
# }