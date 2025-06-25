from google.cloud import batch_v1
from google.protobuf import duration_pb2
import uuid, re
from settings import settings

def submit(scene_id: str, blend_uri: str, webhook: str | None):
    """
    Pure function – mirrors the script you posted.
    `blend_uri` is gs://bucket/path/scene.blend (already uploaded).
    """
    project_id, region, bucket = settings.project_id, settings.region, settings.bucket

    job_id  = f"render-{scene_id}-{uuid.uuid4().hex[:6]}"
    parent  = f"projects/{project_id}/locations/{region}"
    out_uri = f"gs://{bucket}/renders/{scene_id}/"

    m = re.match(r"^gs://([^/]+)/(.+)$", blend_uri)
    scene_bucket, _ = m.group(1), m.group(2)

    # ── shell script ──
    script = f"""set -euo pipefail
cp "/mnt/stateful_partition/in/{scene_id}/scene.blend" scene.blend
blender -b scene.blend -E CYCLES -f 1
OUT_DIR=/mnt/stateful_partition/out/renders/{scene_id}
mkdir -p "$OUT_DIR"
cp Furniture_* Light_* Shadow_* scene.blend "$OUT_DIR/"
if [ -n "{webhook or ''}" ]; then
  apt-get -qq update && apt-get -y install --no-install-recommends curl >/dev/null
  curl -s -X POST -H 'Content-Type: application/json' \
       -d '{{"scene_id":"{scene_id}","status":"done","gcs_prefix":"{out_uri}"}}' \
       "{webhook}"
fi
"""

    client = batch_v1.BatchServiceClient()
    run = batch_v1.Runnable(
        container=batch_v1.Runnable.Container(
            image_uri="docker.io/linuxserver/blender:3.5.0",
            entrypoint="/bin/bash", commands=["-c", script])
    )

    job = batch_v1.Job(
        task_groups=[
            batch_v1.TaskGroup(
                task_spec=batch_v1.TaskSpec(
                    runnables=[run],
                    volumes=[
                        batch_v1.Volume(
                            gcs=batch_v1.GCS(remote_path=scene_bucket),
                            mount_path="/mnt/stateful_partition/in"
                        ),
                        batch_v1.Volume(
                            gcs=batch_v1.GCS(remote_path=bucket),
                            mount_path="/mnt/stateful_partition/out"
                        ),
                    ],
                    compute_resource=batch_v1.ComputeResource(
                        cpu_milli=96_000, memory_mib=384 * 1024),
                    max_run_duration=duration_pb2.Duration(seconds=3600)
                ),
                task_count=1
            )
        ],
        allocation_policy=batch_v1.AllocationPolicy(instances=[
            batch_v1.AllocationPolicy.InstancePolicyOrTemplate(
                policy=batch_v1.AllocationPolicy.InstancePolicy(
                    machine_type="n2-standard-96"))
        ]),
        logs_policy=batch_v1.LogsPolicy(
            destination=batch_v1.LogsPolicy.Destination.CLOUD_LOGGING,
            logs_path="batch_task_logs"
        ),
        labels={"scene": scene_id},
    )

    client.create_job(parent=parent, job=job, job_id=job_id)
