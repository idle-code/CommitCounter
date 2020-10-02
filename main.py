#!/usr/bin/env python
from pathlib import Path
from typing import List

from flask import Request
from datetime import date

from pydantic_settings import BaseSettingsModel, load_settings


class AppSettings(BaseSettingsModel):
    # Enable debug output (logging, additional messages, etc)
    DEBUG: bool = False

    # GitHub access token
    GITHUB_ACCESS_TOKEN: str = "<YOUR_TOKEN_GOES_HERE>"

    # List of repositories to track in "<user>/<repository>" format separated by a colon ':' character
    REPOS_TO_WATCH: str = "user1/repo1:user2/repo2"

    @property
    def REPOS_TO_WATCH_LIST(self) -> List[str]:
        return self.REPOS_TO_WATCH.split(":")

    # Challenge start and end dates in YYYY-MM-DD format
    START_DATE: date = date.fromisoformat("2020-10-10")
    END_DATE: date = date.fromisoformat("2021-10-10")

    # Commits required in challenge
    REQUIRED_COMMIT_COUNT: int = 365

    class Config:
        env_prefix = "CHALLENGE"


def on_request_received(req: Request):
    request_json = req.get_json()

    print(f"Start date: {settings.START_DATE}")
    return f"Repos to watch: {', '.join(settings.REPOS_TO_WATCH_LIST)}"


def serve_flask_endpoint(endpoint):
    from flask import Flask, request
    app = Flask(__name__)
    app.debug = True
    app.route("/")(lambda: endpoint(request))
    app.run()


if __name__ == "__main__":
    settings = load_settings(AppSettings, Path(".env.yaml"))
    serve_flask_endpoint(on_request_received)
else:
    settings = load_settings(AppSettings, "{}", type_hint="json", load_env=True)
