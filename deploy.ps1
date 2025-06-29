# ApplyDesign Blender API - Cloud Run Deployment Script (PowerShell)
# This script builds and deploys the Blender API to Google Cloud Run

# Configuration
$PROJECT_ID = "applydesign"
$REGION = "us-central1"
$SERVICE_NAME = "blender-api"
$IMAGE_NAME = "gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

Write-Host "🚀 Starting deployment of Blender API to Cloud Run..." -ForegroundColor Green

# 1. Set the project
Write-Host "📋 Setting project to ${PROJECT_ID}..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# 2. Enable required APIs
Write-Host "🔧 Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable batch.googleapis.com
gcloud services enable storage.googleapis.com

# 3. Build and deploy to Cloud Run
Write-Host "🏗️  Building and deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
  --source . `
  --platform managed `
  --region $REGION `
  --cpu 8 `
  --memory 16Gi `
  --concurrency 1 `
  --timeout 900 `
  --max-instances 10 `
  --min-instances 0 `
  --allow-unauthenticated `
  --set-env-vars "PROJECT_ID=${PROJECT_ID},REGION=${REGION}" `
  --port 8080

# 4. Get the service URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"

Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host "🌐 Service URL: ${SERVICE_URL}" -ForegroundColor Cyan
Write-Host "🔍 Health check: ${SERVICE_URL}/health" -ForegroundColor Cyan
Write-Host "📚 API docs: ${SERVICE_URL}/docs" -ForegroundColor Cyan

# 5. Test the deployment
Write-Host "🧪 Testing deployment..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
try {
    Invoke-RestMethod -Uri "${SERVICE_URL}/health" -Method Get
    Write-Host "✅ Health check passed!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Health check failed, but service may still be starting up" -ForegroundColor Yellow
}

Write-Host "🎉 Deployment script completed!" -ForegroundColor Green 