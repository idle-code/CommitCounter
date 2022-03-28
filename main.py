#!/usr/bin/env python
import datetime
from dataclasses import InitVar, dataclass, field
from enum import Enum
from math import ceil
from typing import Dict, List, Optional, Tuple

from flask import Request, jsonify, render_template
from github import Github
from github.GithubException import UnknownObjectException
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
    DEBUG_RESULT: ChallengeResult = ChallengeResult.UNKNOWN

    # GitHub access token
    GITHUB_ACCESS_TOKEN: str

    # Repository to track commits from; in "<user>/<repository>" format
    GITHUB_REPO: Optional[str] = None

    # Commits required in challenge
    REQUIRED_COMMIT_COUNT: int = 365

    # Challenge time range
    END_DATE: datetime.datetime = datetime.datetime.now()
    START_DATE: datetime.datetime = END_DATE - datetime.timedelta(
        days=REQUIRED_COMMIT_COUNT
    )


def total_days_between(
    first_date: datetime.datetime, second_date: datetime.datetime
) -> int:
    total_seconds_between = (first_date - second_date).total_seconds()
    return ceil(total_seconds_between / (24 * 60 * 60))


@dataclass
class ChallengeData:
    required_commit_count: int
    start_date: datetime.datetime
    end_date: datetime.datetime
    today: InitVar[datetime.datetime]
    repo: Optional[str] = None

    state: ChallengeState = field(init=False)
    days_from_start: int = field(init=False)
    days_to_end: int = field(init=False)
    total_days: int = field(init=False)

    def __post_init__(self, today: datetime.datetime):
        if today < self.start_date:
            self.state = ChallengeState.PENDING
        elif today < self.end_date:
            self.state = ChallengeState.IN_PROGRESS
        else:
            self.state = ChallengeState.FINISHED
        self.days_from_start = total_days_between(today, self.start_date)
        self.days_to_end = total_days_between(self.end_date, today)
        self.total_days = total_days_between(self.end_date, self.start_date)


@dataclass
class ChallengeStatus:
    commits_done: int
    commits_todo: int
    percentage_done: float


@dataclass
class ChallengeStatistics:
    commit_count: int
    actual: ChallengeStatus = field(init=False)
    expected: ChallengeStatus = field(init=False)
    result: ChallengeResult = field(init=False)
    commit_difference: int = field(init=False)
    challenge: InitVar[ChallengeData]

    def __post_init__(self, challenge: ChallengeData):
        self.actual = ChallengeStatus(
            commits_done=self.commit_count,
            commits_todo=challenge.required_commit_count - self.commit_count,
            percentage_done=min(
                100.0 * self.commit_count / challenge.required_commit_count, 100.0
            ),
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
            percentage_done=min(
                100.0 * commits_done / challenge.required_commit_count, 100.0
            ),
        )

        if self.actual.commits_done >= challenge.required_commit_count:
            self.result = ChallengeResult.SUCCEEDED
        elif challenge.state == ChallengeState.FINISHED:
            self.result = ChallengeResult.FAILED
        else:
            self.result = ChallengeResult.UNKNOWN

        self.commit_difference = self.actual.commits_done - self.expected.commits_done


def on_request_received(req: Request):
    print(f"Start date: {settings.START_DATE}")
    print(f"End date: {settings.END_DATE}")

    if settings.DEBUG:
        assert settings.DEBUG_STATE
        challenge_data, stats = generate_fake_challenge_stats(
            settings.DEBUG_STATE, settings.DEBUG_RESULT
        )
    else:
        challenge_data = ChallengeData(
            required_commit_count=settings.REQUIRED_COMMIT_COUNT,
            start_date=settings.START_DATE,
            end_date=settings.END_DATE,
            today=datetime.datetime.now(),
            repo=settings.GITHUB_REPO,
        )
        if challenge_data.state == ChallengeState.PENDING:
            commit_count = 0
        elif settings.GITHUB_REPO:
            commit_count = len(fetch_commits_in_repo(settings.GITHUB_REPO))
        else:
            commit_count = len(fetch_commits())
        stats = ChallengeStatistics(challenge=challenge_data, commit_count=commit_count)

    if "json" in req.args:
        return jsonify({"challenge": challenge_data, "stats": stats})
    else:
        if stats.result == ChallengeResult.SUCCEEDED:
            template_name = "succeeded.jinja2.html"
        elif stats.result == ChallengeResult.FAILED:
            template_name = "failed.jinja2.html"
        elif challenge_data.state == ChallengeState.PENDING:
            template_name = "pending.jinja2.html"
        elif challenge_data.state == ChallengeState.IN_PROGRESS:
            template_name = "in_progress.jinja2.html"
        else:
            raise NotImplementedError("Unknown status - cannot choose correct template")

        return render_template(
            template_name,
            challenge=challenge_data,
            stats=stats,
            debug=settings.DEBUG,
        )


def generate_fake_challenge_stats(
    state: ChallengeState, result: ChallengeResult
) -> Tuple[ChallengeData, ChallengeStatistics]:
    if result != ChallengeResult.SUCCEEDED:
        commits_done = 3
        required_commits = 5
    else:
        commits_done = 6
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
        today=today,
    )

    stats = ChallengeStatistics(challenge=challenge_data, commit_count=commits_done)
    return challenge_data, stats


def fetch_commits():
    repositories = find_user_repositories()
    print(f"Found {repositories.totalCount} repositories")

    all_commits = []
    for repo in repositories:
        try:
            commits_in_repo = fetch_commits_in_repo(repo.name)
            all_commits.extend(commits_in_repo)
        except UnknownObjectException:
            print(f"Exception while fetching {repo}")

    print(f"Total commits in found all repositories: {len(all_commits)}")
    return all_commits


def find_user_repositories():
    github = Github(settings.GITHUB_ACCESS_TOKEN)
    user = github.get_user()
    print(f"Looking for repos of user: {user}")
    repositories = user.get_repos()
    return repositories


def fetch_commits_in_repo(repo_name, author=None):
    github = Github(settings.GITHUB_ACCESS_TOKEN)
    user = github.get_user()
    repo = user.get_repo(repo_name)
    if author is None:
        author = repo.owner
    commits_in_repo = repo.get_commits(
        since=settings.START_DATE, until=settings.END_DATE, author=author
    )
    print(f"Found {commits_in_repo.totalCount} commits in {repo_name}")
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
