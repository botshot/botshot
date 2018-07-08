from django.http import HttpResponse
from django.shortcuts import render


def string_view(req):
    strings = [
        {
            "key": "MY_STR",
            "value": "My string"
        },
        {
            "key": "MY_STR",
            "value": "My string"
        },
        {
            "key": "MY_STR",
            "value": "My string"
        }
    ]
    return render(req, "botshot/strings/index.html", context={"strings": strings})


def detail_view(req, key):
    string = {
        "key": "MY_STR",
        "value": "My string"
    }
    if not key: string = None
    return render(req, "botshot/strings/detail.html", context={"string": string})
