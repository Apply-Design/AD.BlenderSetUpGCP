from google.cloud import batch_v1
from google.protobuf import duration_pb2
import uuid, re
from settings import settings
import logging

logger = logging.getLogger("batch_submit")

def submit(scene_id: str, blend_uri: str, webhook: str | None):
    """
    Launch a render job that reads the .blend we uploaded to
    gs://<bucket>/renders/<scene_id>/<scene_id>.blend
    """
    project_id, region, bucket = (
        settings.project_id,
        settings.region,
        settings.bucket,
    )

    job_id = f"render-{scene_id}-{uuid.uuid4().hex[:6]}"
    parent = f"projects/{project_id}/locations/{region}"
    out_uri = f"gs://{bucket}/renders/{scene_id}/"

    # input bucket name only (Batch needs just the bucket, not the object path)
    m = re.match(r"^gs://([^/]+)/.+$", blend_uri)
    scene_bucket = m.group(1)

    # ── shell script executed inside the Batch VM ──────────────────────────
    script = f"""\
set -euo pipefail

# 1) copy the uploaded blend (renders/<id>/<id>.blend) to ./scene.blend
echo "📂  Copying .blend from renders/{scene_id}/{scene_id}.blend"
cp "/mnt/stateful_partition/in/renders/{scene_id}/{scene_id}.blend" scene.blend

# 2) render a single frame (CPU)
echo "🎬  Rendering frame 1"
blender -b scene.blend -E CYCLES -f 1

# 3) copy outputs back to out bucket
OUT_DIR=/mnt/stateful_partition/out/renders/{scene_id}
mkdir -p "$OUT_DIR"
cp Furniture_* Light_* Shadow_* scene.blend "$OUT_DIR/"

# 4) optional webhook
if [ -n "{webhook or ''}" ]; then
  apt-get -qq update && apt-get -y install --no-install-recommends curl >/dev/null
  curl -X POST -d '{{"workflow_id": "{job_id}"}}' -H "Content-Type: application/json" {settings.pipeline_manager_url}/actions/signal/rendering_process_post_blender
fi
"""

    # ── Batch API objects ───────────────────────────────────────────────────
    client = batch_v1.BatchServiceClient()

    run = batch_v1.Runnable(
        container=batch_v1.Runnable.Container(
            image_uri="docker.io/linuxserver/blender:3.5.0",
            entrypoint="/bin/bash",
            commands=["-c", script],
        )
    )

    job = batch_v1.Job(
        task_groups=[
            batch_v1.TaskGroup(
                task_spec=batch_v1.TaskSpec(
                    runnables=[run],
                    volumes=[
                        # INPUT  (mount entire bucket)
                        batch_v1.Volume(
                            gcs=batch_v1.GCS(remote_path=scene_bucket),
                            mount_path="/mnt/stateful_partition/in",
                        ),
                        # OUTPUT (same bucket, but we'll write via renders/<id>/)
                        batch_v1.Volume(
                            gcs=batch_v1.GCS(remote_path=bucket),
                            mount_path="/mnt/stateful_partition/out",
                        ),
                    ],
                    compute_resource=batch_v1.ComputeResource(
                        cpu_milli=96_000,
                        memory_mib=384 * 1024,
                    ),
                    max_run_duration=duration_pb2.Duration(seconds=3600),
                ),
                task_count=1,
            )
        ],
        allocation_policy=batch_v1.AllocationPolicy(
            instances=[
                batch_v1.AllocationPolicy.InstancePolicyOrTemplate(
                    policy=batch_v1.AllocationPolicy.InstancePolicy(
                        machine_type="n2-standard-96"
                    )
                )
            ]
        ),
        logs_policy=batch_v1.LogsPolicy(
            destination=batch_v1.LogsPolicy.Destination.CLOUD_LOGGING,
            logs_path="batch_task_logs",
        ),
        labels={"scene": scene_id},
    )

    logger.info(f"Batch job object created for scene_id=%s, job_id=%s", scene_id, job_id)
    client.create_job(parent=parent, job=job, job_id=job_id)
    logger.info(f"Batch job submitted for scene_id=%s, job_id=%s", scene_id, job_id)
