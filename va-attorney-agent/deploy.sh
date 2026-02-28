#!/usr/bin/env bash
#
# Deploy va-attorney-agent to GCP Cloud Run.
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated
#   2. ANTHROPIC_API_KEY stored in Secret Manager:
#      gcloud secrets create ANTHROPIC_API_KEY --data-file=-  <<< "sk-ant-..."
#   3. Artifact Registry repository created:
#      gcloud artifacts repositories create va-attorney --location=us-central1 --repository-format=docker
#
# Usage:
#   ./deploy.sh                     # uses defaults
#   PROJECT_ID=my-proj ./deploy.sh  # override project

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-va-attorney-agent}"
REPO_NAME="${REPO_NAME:-va-attorney}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"

echo "=== Building container image ==="
echo "  Image: ${IMAGE}"

gcloud builds submit \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --tag="${IMAGE}" \
  .

echo ""
echo "=== Deploying to Cloud Run ==="

gcloud run deploy "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${IMAGE}" \
  --platform=managed \
  --memory=2Gi \
  --cpu=2 \
  --timeout=900 \
  --concurrency=1 \
  --min-instances=0 \
  --max-instances=10 \
  --set-secrets="ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest" \
  --set-env-vars="BVA_API_BASE_URL=https://bva-api-524576132881.us-central1.run.app" \
  --allow-unauthenticated

echo ""
echo "=== Deployment complete ==="
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format="value(status.url)")
echo "  Service URL: ${SERVICE_URL}"
echo "  Health check: curl ${SERVICE_URL}/health"
