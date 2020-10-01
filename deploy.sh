#!/usr/bin/env bash

# Generate requirements.txt file
poetry export --format requirements.txt > requirements.txt

# Upload source code to the GCP
gcloud functions deploy \
  count_commits \
  --allow-unauthenticated \
  --entry-point=count_commits \
  --runtime python38 \
  --trigger-http
#  --env-vars-file=.env \


