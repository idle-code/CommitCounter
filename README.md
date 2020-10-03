## Commit counter for 365 Commits Challenge
Commit Counter generates simple webpage for tracking progress of 365 Commits Challenge.
It can be easily deployed as Google Cloud Function. All you need is to:
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
   # Check project on what project you are currently on:
   gcloud config list
   # Make sure you have set correct functions/region:
   gcloud config set functions/region <region-close-to-you>
   ```
6. Deploy solution by executing `deploy.sh` script:
    ```shell script
    ./deploy.sh
    ```
7. Visit function endpoint with webbrowser and start coding!
