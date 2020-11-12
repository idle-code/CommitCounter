## Commit counter for 365 Commits Challenge
Commit Counter generates simple webpage for tracking your progress in 365 Commits Challenge.
It can be easily deployed as Google Cloud Function.

## Requirements
- Python 3.8 or newer
- [poetry](https://python-poetry.org/)
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)

## Deployment
1. Create `.env.yaml` config file from the provided template template:
   ```shell script
   cp .env.yaml.template .env.yaml
   ```
2. Generate GitHub access token: \
   Go to your GitHub's *Settings > Developer Settings > Personal access tokens* or click [here](https://github.com/settings/tokens). \
   Generate new token with `repo` and `user` permissions.
3. Put generated token into `GITHUB_ACCESS_TOKEN` variable in `.env.yaml` file.
4. Adjust start, end and commit count settings in `.env.yaml` file.\
   Note: Make sure that all values are strings.
5. Make sure your `gcloud` configuration is correct:
   ```shell script
   # Check your active project:
   gcloud config list
   # Make sure you have set correct region for function deployment:
   # Note: compute/region doesn't affect functions.
   gcloud config set functions/region <region-close-to-you>
   ```
6. Deploy solution by executing `deploy.sh` script:
    ```shell script
    ./deploy.sh
    ```
7. Visit function endpoint with webbrowser and start coding!

## ToDo/Backlog
- [ ] Display challenge info
    - [ ] Start/end date
    - [ ] Commits left
    - [ ] Days to go
    - [ ] Current progress
    - [ ] Nice progress bar
- [ ] Group commits shown by date and repository
- [ ] Serve placeholder site when visiting root page and update commit data interactively.
- [ ] Add setting for holding repo blacklist - repositories that should not count in the challenge.
- [ ] Rename `START_DATE`/`END_DATE` to `CHALLENGE_START`/`CHALLENGE_END`.
- [ ] Make use of `DEBUG` setting.
- [ ] Generate `.env.yaml` by `main.py --generate-settings` (or similar) invocation - get rid of template.
