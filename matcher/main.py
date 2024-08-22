"""
Set up matchers to return mock responses for certain URL requests (or forward them if no match is found)

Author: Ryan Basso
"""

import json
import re
import time
from mitmproxy import http

# A class to load the matcher file
# (this ensures it is only opened and initialized once per program run - we don't want
# to be constantly opening up files on every single request we get)
class Singleton:
    _instance = None
    _matcher = None

    # Constructor for singleton
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)

            # Read file contents
            file = open("matcher.json")
            contents = file.read()
            file.close()

            # Save matcher for use later:
            cls._matcher = json.loads(contents)
        return cls._instance

# What mitmproxy's Python runtime calls on each request it intercepts
# (this will either forward the request to the real server or modify
# it if we hit a match from the requestMapper instance)
def request(flow: http.HTTPFlow) -> None:

    # Initialize singleton (if not created yet)
    requestMapper = Singleton()

    # Iterate over request types to load a corresponding mock response
    for match in requestMapper._matcher:
        check1 = match["method"] == flow.request.method
        check2 = re.search(match["urlRegex"], flow.request.pretty_url)
        check3 = match["enabled"] == True
        if check1 and check2 and check3: 
            # Open mock response corresponding to match found
            file = open(match["mockResponsePath"])
            contents = file.read()
            file.close()
            
            # Load response and body values
            mockResponse = json.loads(contents)
            body = json.dumps(mockResponse["body"])

            # Note: This field can make it much easier to both (1) observe any loading spinners from a UI-review perspective
            # as well as (2) force a SocketTimeoutException (or equivalent) to see if the app handles timeout errors gracefully.
            delayMillis = mockResponse["delayMillis"]

            # Simulate network delay
            time.sleep(delayMillis / 1000)

            # Modify response according to file contents
            flow.response = http.Response.make(
                mockResponse["code"],
                f"{body}",
                mockResponse["headers"]
            )