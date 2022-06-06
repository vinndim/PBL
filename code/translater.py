import requests
import urllib


def translate(query, lang):
    url = "https://translated-mymemory---translation-memory.p.rapidapi.com/api/get"
    querystring = {"q": query, "langpair": lang, "de": "a@b.c", "onlyprivate": "0", "mt": "1"}

    headers = {
        "X-RapidAPI-Host": "translated-mymemory---translation-memory.p.rapidapi.com",
        "X-RapidAPI-Key": "e581e3088fmsh8c9e3178380f25fp1c9b68jsnc45f93733834"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    return response.json()["responseData"]["translatedText"]