#!/usr/bin/env python
from flask import Request


def count_commits(request: Request):
    request_json = request.get_json()
    if request.args and 'message' in request.args:
        return request.args.get('message')
    elif request_json and 'message' in request_json:
        return request_json['message']
    else:
        return f'Hello World!'


if __name__ == "__main__":
    # TODO: start sample server?
    print(count_commits(Request({})))

