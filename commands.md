# Commands

## Docker Operations

### Build Docker Image
```bash
docker build -t applydesign-render .
```

### Run Docker Container Locally
```bash
docker run -p 8080:8080 \
  -v "C:\Users\yaniv\AppData\Roaming\gcloud:/adc:ro" \
  -e GOOGLE_APPLICATION_CREDENTIALS=/adc/application_default_credentials.json \
  -e PROJECT_ID=applydesign \
  -e REGION=us-central1 \
  -e BLENDER_EXE_LOCATION=/usr/local/bin/blender \
  applydesign-render
```

## Testing

### Run Test Command Locally
```bash
python test/send_request.py
```

### Build for cloud
```bash
gcloud builds submit --tag gcr.io/applydesign/blender-api
```
### Deploy to cloud
```bash
gcloud run deploy blender-api --image gcr.io/applydesign/blender-api --platform managed --region us-central1 --cpu 8 --memory 16Gi  --concurrency 1 --timeout 900
```