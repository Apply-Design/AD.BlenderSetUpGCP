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
