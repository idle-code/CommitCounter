#!/usr/bin/env bash

# Generate requirements.txt file
echo "Generating requirements.txt..."
poetry export --format requirements.txt > requirements.txt

# Check existence of file with environment variables
ENV_YAML_FILE=".env.yaml"
if [ ! -f "$ENV_YAML_FILE" ]; then
  echo "Missing $ENV_YAML_FILE file - please create one from template before trying again"
  exit 1
fi

# Upload source code to the GCP
echo "Deploying to GCP..."
gcloud functions deploy \
  count_commits \
  --allow-unauthenticated \
  --entry-point=on_request_received \
  --runtime python38 \
  --memory=128MB \
  --env-vars-file=$ENV_YAML_FILE \
  --trigger-http
