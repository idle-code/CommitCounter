#!/usr/bin/env python
from dataclasses import dataclass, field, InitVar
from enum import Enum
from math import ceil
from typing import Optional, Dict, List

from flask import Request, render_template, jsonify
import datetime
from pydantic import BaseSettings


class ChallengeState(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class ChallengeResult(str, Enum):
    UNKNOWN = "unknown"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AppSettings(BaseSettings):
    # Enable debug output (logging, additional messages, etc)
    DEBUG: bool = False

    DEBUG_STATE: Optional[ChallengeState] = None

    # GitHub access token
    GITHUB_ACCESS_TOKEN: str

    # Commits required in challenge
    REQUIRED_COMMIT_COUNT: int = 365

    # Challenge time range
    END_DATE: datetime.datetime = datetime.datetime.now()
    START_DATE: datetime.datetime = END_DATE - datetime.timedelta(days=REQUIRED_COMMIT_COUNT)


@dataclass
class ChallengeData:
    required_commit_count: int
    start_date: datetime.datetime
    end_date: datetime.datetime
    state: ChallengeState = field(init=False)
    days_from_start: int = field(init=False)
    days_to_end: int = field(init=False)
    total_days: int = field(init=False)

    today: InitVar[datetime.datetime]

    def __post_init__(self, today: datetime.datetime):
        if today < self.start_date:
            self.state = ChallengeState.PENDING
        elif today < self.end_date:
            self.state = ChallengeState.IN_PROGRESS
        else:
            self.state = ChallengeState.FINISHED
        self.days_from_start = (today - self.start_date).days
        self.days_to_end = (self.end_date - today).days
        self.total_days = (self.end_date - self.start_date).days


@dataclass
class ChallengeStatus:
    commits_done: int
    commits_todo: int
    percentage_done: float


@dataclass
class ChallengeStatistics:
    commits: List
    actual: ChallengeStatus = field(init=False)
    expected: ChallengeStatus = field(init=False)
    result: ChallengeResult = field(init=False)
    commit_difference: int = field(init=False)
    challenge: InitVar[ChallengeData]

    def __post_init__(self, challenge: ChallengeData):
        commits_done = len(self.commits)
        self.actual = ChallengeStatus(
            commits_done=commits_done,
            commits_todo=challenge.required_commit_count - commits_done,
            percentage_done=100.0 * commits_done / challenge.required_commit_count
        )

        commits_per_day = challenge.required_commit_count / challenge.total_days
        if challenge.state == ChallengeState.FINISHED:
            commits_done = challenge.required_commit_count
        elif challenge.state == ChallengeState.IN_PROGRESS:
            commits_done = ceil(challenge.days_from_start * commits_per_day)
        else:
            commits_done = 0
        self.expected = ChallengeStatus(
            commits_done=commits_done,
            commits_todo=challenge.required_commit_count - commits_done,
            percentage_done=100.0 * commits_done / challenge.required_commit_count
        )

        if challenge.state in (ChallengeState.PENDING, ChallengeState.IN_PROGRESS):
            self.result = ChallengeResult.UNKNOWN
        else:
            if self.actual.commits_done >= challenge.required_commit_count:
                self.result = ChallengeResult.SUCCEEDED
            else:
                self.result = ChallengeResult.FAILED

        self.commit_difference = self.actual.commits_done - self.expected.commits_done


def on_request_received(req: Request):
    print(f"Start date: {settings.START_DATE}")
    print(f"End date: {settings.END_DATE}")

    if settings.DEBUG:
        assert settings.DEBUG_STATE
        challenge_data, stats = generate_fake_challenge_stats(settings.DEBUG_STATE)
    else:
        challenge_data = ChallengeData(
            required_commit_count=settings.REQUIRED_COMMIT_COUNT,
            start_date=settings.START_DATE,
            end_date=settings.END_DATE,
            today=datetime.datetime.now()
        )
        commits = fetch_commits()
        stats = ChallengeStatistics(challenge=challenge_data, commits=commits)

    if "json" in req.args:
        return jsonify({
            "challenge": challenge_data,
            "stats": stats
        })
    else:
        return render_template("index.jinja2.html", challenge=challenge_data, stats=stats, debug=settings.DEBUG)


def generate_fake_challenge_stats(state: ChallengeState, result: ChallengeResult = ChallengeResult.UNKNOWN) -> ChallengeStatistics:
    if result != ChallengeResult.SUCCEEDED:
        commits = [1, 2, 3]
        required_commits = 5
    else:
        commits = [1, 2, 3, 4, 5, 6]
        required_commits = 5

    today = datetime.datetime.now()
    if state == ChallengeState.PENDING:
        start_date = today + datetime.timedelta(days=10)
        end_date = today + datetime.timedelta(days=20)
    elif state == ChallengeState.IN_PROGRESS:
        start_date = today - datetime.timedelta(days=10)
        end_date = today + datetime.timedelta(days=10)
    elif state == ChallengeState.FINISHED:
        start_date = today - datetime.timedelta(days=20)
        end_date = today - datetime.timedelta(days=10)
    else:
        raise NotImplementedError()

    challenge_data = ChallengeData(
        required_commit_count=required_commits,
        start_date=start_date,
        end_date=end_date,
        today=today
    )

    stats = ChallengeStatistics(challenge=challenge_data, commits=commits)
    return challenge_data, stats


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

