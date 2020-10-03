#!/usr/bin/env python
from pathlib import Path
from flask import Request
import datetime

from pydantic_settings import BaseSettingsModel, load_settings


class AppSettings(BaseSettingsModel):
    # Enable debug output (logging, additional messages, etc)
    DEBUG: bool = False

    # GitHub access token
    GITHUB_ACCESS_TOKEN: str

    # Challenge start and end dates in YYYY-MM-DD format
    START_DATE: datetime.datetime = datetime.datetime.now()
    END_DATE: datetime.datetime = datetime.datetime.now() + datetime.timedelta(days=365)

    # Commits required in challenge
    REQUIRED_COMMIT_COUNT: int = 365


def on_request_received(req: Request):
    if "days" in req.args:
        days_to_display = int(req.args["days"])
        settings.END_DATE = datetime.datetime.now()
        settings.START_DATE = datetime.datetime.now() - datetime.timedelta(days=days_to_display)

    print(f"Start date: {settings.START_DATE}")
    print(f"End date: {settings.END_DATE}")

    commits = fetch_commits()

    # TODO: generate proper Jinja template

    commits_message = ""
    for c in commits:
        commits_message += f"{c.url}</br>"

    return f"<html><body>{commits_message}</body></html>"


def fetch_commits():
    from github import Github
    github = Github(settings.GITHUB_ACCESS_TOKEN)

    user = github.get_user()
    print(f"Looking for repos of user: {user}")
    repositories = user.get_repos()
    print(f"Found {repositories.totalCount} repositories")

    all_commits = []
    for repo in repositories:
        commits_in_repo = fetch_commits_in_repo(repo)
        if commits_in_repo:
            print(f"Adding {len(commits_in_repo)} commits")
            all_commits.extend(commits_in_repo)

    print(f"Total commits in found all repositories: {len(all_commits)}")
    return all_commits


def fetch_commits_in_repo(repo):
    print(f"Checking repository {repo}...")
    commits_in_repo = repo.get_commits(since=settings.START_DATE, until=settings.END_DATE, author=repo.owner)
    return list(commits_in_repo)


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
