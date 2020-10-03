#!/usr/bin/env python
from pathlib import Path
from flask import Request, render_template
import datetime
from pydantic import BaseSettings


class AppSettings(BaseSettings):
    # Enable debug output (logging, additional messages, etc)
    DEBUG: bool = False

    # GitHub access token
    GITHUB_ACCESS_TOKEN: str

    # Commits required in challenge
    REQUIRED_COMMIT_COUNT: int = 365

    # Challenge start and end dates in YYYY-MM-DD format
    END_DATE: datetime.datetime = datetime.datetime.now()
    START_DATE: datetime.datetime = END_DATE - datetime.timedelta(days=REQUIRED_COMMIT_COUNT)


def on_request_received(req: Request):
    if "days" in req.args:
        days_to_display = int(req.args["days"])
        print(f"Looking only {days_to_display} days behind")
        settings.END_DATE = datetime.datetime.now()
        settings.START_DATE = settings.END_DATE - datetime.timedelta(days=days_to_display)

    print(f"Start date: {settings.START_DATE}")
    print(f"End date: {settings.END_DATE}")

    commits = fetch_commits()

    commits_message = ""
    for c in commits:
        commits_message += f"{c.url}</br>"

    return render_template("index.jinja2.html", settings=settings, commits=commits)


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
        all_commits.extend(commits_in_repo)

    print(f"Total commits in found all repositories: {len(all_commits)}")
    return all_commits


def fetch_commits_in_repo(repo):
    commits_in_repo = repo.get_commits(since=settings.START_DATE, until=settings.END_DATE, author=repo.owner)
    print(f"Found {commits_in_repo.totalCount} commits in {repo}")
    return list(commits_in_repo)


def serve_flask_endpoint(endpoint):
    from flask import Flask, request
    app = Flask(__name__)
    app.debug = True
    app.route("/")(lambda: endpoint(request))
    app.run()


def load_settings_from_environment() -> AppSettings:
    return AppSettings()


def load_settings_from_yaml(yaml_path: str) -> AppSettings:
    import yaml
    with open(yaml_path) as yaml_file:
        yaml_env = yaml.safe_load(yaml_file)
        return AppSettings(**yaml_env)


if __name__ == "__main__":
    settings = load_settings_from_yaml(".env.yaml")
    serve_flask_endpoint(on_request_received)
else:
    settings = load_settings_from_environment()

