from fastapi import FastAPI, HTTPException
from models.scene import PostData
from uuid import uuid4
from google.cloud import storage
from services.scene_builder import build_scene
from services.batch_submit import submit
from settings import settings

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "service": "blender-api"}

@app.post("/render")
async def render(data: PostData):
    scene_id = data.scene_id if hasattr(data, "scene_id") else uuid4().hex[:8]  # optional
    local_blend = await build_scene(data, scene_id)

    # upload
    uri = await _upload(local_blend, scene_id)

    # fire-and-forget submit
    submit(scene_id, uri, data.webhook)

    return {"scene_id": scene_id, "blend": uri, "status": "submitted"}

async def _upload(path, scene_id):
    client = storage.Client(project=settings.project_id)
    bucket = client.bucket(settings.bucket)
    blob   = bucket.blob(f"renders/{scene_id}/{scene_id}.blend")
    blob.upload_from_filename(path)
    return f"gs://{settings.bucket}/renders/{scene_id}/{scene_id}.blend"
