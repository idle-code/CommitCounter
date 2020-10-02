#!/usr/bin/env bash

# Generate requirements.txt file
echo "Generating requirements.txt..."
poetry export --format requirements.txt > requirements.txt

# Upload source code to the GCP
echo "Deploying to GCP..."
gcloud functions deploy \
  count_commits \
  --allow-unauthenticated \
  --entry-point=on_request_received \
  --runtime python38 \
  --memory=128MB \
  --env-vars-file=.env.yaml \
  --trigger-http


