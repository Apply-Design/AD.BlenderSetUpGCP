# Cloud Run Deployment Guide

This guide explains how to deploy the ApplyDesign Blender API to Google Cloud Run.

## Prerequisites

1. **Google Cloud SDK** installed and configured
2. **Docker** installed (for local testing)
3. **Google Cloud Project** with billing enabled
4. **Service Account** with necessary permissions

## Required Permissions

Your service account needs these roles:
- Cloud Run Admin
- Cloud Build Editor
- Storage Admin
- Batch Job Admin
- Service Account User

## Deployment Options

### Option 1: Quick Deploy (Recommended)

Use the provided deployment script:

```bash
# Make the script executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

### Option 2: Manual Deployment

1. **Set your project:**
   ```bash
   gcloud config set project applydesign
   ```

2. **Enable required APIs:**
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable batch.googleapis.com
   gcloud services enable storage.googleapis.com
   ```

3. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy blender-api \
     --source . \
     --platform managed \
     --region us-central1 \
     --cpu 8 \
     --memory 16Gi \
     --concurrency 1 \
     --timeout 900 \
     --max-instances 10 \
     --min-instances 0 \
     --allow-unauthenticated
   ```

### Option 3: Cloud Build (CI/CD)

For automated deployments, use Cloud Build:

```bash
# Trigger build
gcloud builds submit --config cloudbuild.yaml
```

## Resource Configuration

### Current Settings
- **CPU**: 8 vCPUs (required for Blender operations)
- **Memory**: 16 GB RAM (Blender + Python dependencies)
- **Concurrency**: 1 (CPU-intensive operations)
- **Timeout**: 900 seconds (15 minutes)
- **Max Instances**: 10 (scale limit)
- **Min Instances**: 0 (cost optimization)

### Scaling Considerations

**High Traffic:**
- Increase `max-instances` to 20-50
- Consider `min-instances: 1` for faster cold starts

**Cost Optimization:**
- Reduce `max-instances` to 5
- Keep `min-instances: 0`
- Monitor usage patterns

## Environment Variables

The following environment variables are automatically set:
- `PROJECT_ID`: Your GCP project ID
- `REGION`: us-central1
- `PORT`: 8080 (Cloud Run requirement)

Additional variables can be set via `--set-env-vars`:
```bash
--set-env-vars "CUSTOM_VAR=value,ANOTHER_VAR=value2"
```

## Monitoring & Logging

### View Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blender-api" --limit=50
```

### Monitor Performance
- Use Cloud Run console for metrics
- Set up alerts for error rates
- Monitor memory and CPU usage

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Dockerfile syntax
   - Verify all dependencies in requirements.txt
   - Ensure sufficient disk space for build

2. **Runtime Errors**
   - Check application logs
   - Verify environment variables
   - Ensure proper permissions

3. **Performance Issues**
   - Increase CPU/memory allocation
   - Optimize Blender scene complexity
   - Review concurrency settings

### Health Checks

The service includes a health check endpoint:
```
GET /health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "blender-api"
}
```

## Cost Optimization

1. **Right-size resources** based on actual usage
2. **Use min-instances: 0** for cost savings
3. **Monitor and adjust** max-instances
4. **Consider regional pricing** differences

## Security

1. **Authentication**: Currently set to `--allow-unauthenticated`
2. **For production**: Implement proper authentication
3. **Service accounts**: Use least privilege principle
4. **Network security**: Consider VPC connector if needed

## Updates & Rollbacks

### Update Service
```bash
gcloud run deploy blender-api --source .
```

### Rollback
```bash
gcloud run revisions list --service=blender-api
gcloud run services update-traffic blender-api --to-revisions=REVISION_NAME=100
```

## Support

For issues related to:
- **Cloud Run**: Check Google Cloud documentation
- **Application**: Review logs and error messages
- **Blender**: Verify scene complexity and resource requirements 