from fastapi import FastAPI, HTTPException
from models.scene import PostData
from google.cloud import storage
from services.scene_builder import build_scene, cleanup_temp_files
from services.batch_submit import submit
from settings import settings
import logging

logger = logging.getLogger("main")

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "service": "blender-api"}

@app.post("/render")
async def render(data: PostData):
    # Use render_job_id as the only ID throughout the system
    render_job_id = str(data.render_job_id)
    
    try:
        local_blend = await build_scene(data, render_job_id)

        # upload
        uri = await _upload(local_blend, render_job_id)

        # fire-and-forget submit
        batch_job_name = submit(render_job_id, uri, data.webhook)

        logger.info(f"Successfully submitted render job for render_job_id=%s", render_job_id)
        return {
            "render_job_id": render_job_id,
            "blend": uri,
            "batch_job": batch_job_name,
            "status": "submitted",
        }
        
    except Exception as e:
        logger.error(f"Error processing render job for render_job_id=%s: %s", render_job_id, e)
        raise HTTPException(status_code=500, detail=f"Render job failed: {str(e)}")
    finally:
        # Always cleanup temporary files, even if there was an error
        try:
            cleanup_temp_files(render_job_id)
            logger.info(f"Cleaned up temporary files for render_job_id=%s", render_job_id)
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup temp files for render_job_id=%s: %s", render_job_id, cleanup_error)

async def _upload(path, render_job_id):
    client = storage.Client(project=settings.project_id)
    bucket = client.bucket(settings.bucket)
    blob   = bucket.blob(f"renders/{render_job_id}/{render_job_id}.blend")
    blob.upload_from_filename(path)
    return f"gs://{settings.bucket}/renders/{render_job_id}/{render_job_id}.blend"
