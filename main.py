#!/usr/bin/env python
from enum import Enum

from flask import Request, render_template, jsonify
import datetime
from pydantic import BaseSettings


class AppSettings(BaseSettings):
    # Enable debug output (logging, additional messages, etc)
    DEBUG: bool = False

    # GitHub access token
    GITHUB_ACCESS_TOKEN: str

    # Commits required in challenge
    REQUIRED_COMMIT_COUNT: int = 365

    # Challenge time range
    END_DATE: datetime.datetime = datetime.datetime.now()
    START_DATE: datetime.datetime = END_DATE - datetime.timedelta(days=REQUIRED_COMMIT_COUNT)


class ChallengeStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


def on_request_received(req: Request):
    if "days" in req.args:  # TODO: remove if not used
        days_to_display = int(req.args["days"])
        print(f"Looking only {days_to_display} days behind")
        settings.END_DATE = datetime.datetime.now()
        settings.START_DATE = settings.END_DATE - datetime.timedelta(days=days_to_display)

    print(f"Start date: {settings.START_DATE}")
    print(f"End date: {settings.END_DATE}")

    if settings.DEBUG:
        commits = []
    else:
        commits = fetch_commits()

    commits_message = ""
    for c in commits:
        commits_message += f"{c.url}</br>"

    today = datetime.datetime.now()

    commits_per_day = settings.REQUIRED_COMMIT_COUNT / (settings.END_DATE - settings.START_DATE).days
    challenge_days_done = (today - settings.START_DATE).days
    commits_done = len(commits)
    expected_commit_count = int(commits_per_day * challenge_days_done)

    if today < settings.START_DATE:
        # TODO: Before start there is no need to fetch commits
        status = ChallengeStatus.PENDING
        days_left = (settings.START_DATE - today).days
    elif commits_done >= settings.REQUIRED_COMMIT_COUNT:
        status = ChallengeStatus.SUCCEEDED
        days_left = (today - settings.END_DATE).days
    elif today < settings.END_DATE:
        status = ChallengeStatus.IN_PROGRESS
        days_left = (settings.END_DATE - today).days
    else:
        status = ChallengeStatus.FAILED
        days_left = (today - settings.END_DATE).days

    challenge_data = {
        "today": today,
        "start": settings.START_DATE,
        "end": settings.END_DATE,
        "days_left": days_left,
        "progress_percentage": 100 * commits_done / settings.REQUIRED_COMMIT_COUNT,
        "expected_progress_percentage": 100 * expected_commit_count / settings.REQUIRED_COMMIT_COUNT,
        "expected_commit_count": expected_commit_count,
        "commits_to_make": settings.REQUIRED_COMMIT_COUNT,
        "commits_done": commits_done,
        "commit_difference": commits_done - expected_commit_count,
        "status": status.value
    }

    if "json" in req.args:
        return jsonify(challenge_data)
    else:
        return render_template("index.jinja2.html", challenge=challenge_data, commits=commits)


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

