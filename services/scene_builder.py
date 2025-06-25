from __future__ import annotations
import asyncio, aiohttp, tempfile, subprocess, json, logging
from pathlib import Path
from typing import List, Tuple

from models.scene import PostData, SceneObjectData
from settings import settings

logger = logging.getLogger("scene_builder")

# ────────────────────────── constants (same names as C#) ──────────────────────────
TEMP_MODELS_DIR       = "tmp/models/"
TEMP_SCENE_DIR        = "tmp/scene/"
TEMP_BFILE_DIR        = "tmp/bfile/"
TEMP_BFILE_TEMPLATE   = "tmp/bfile/scene{0}.blend"
TEMP_CFG_DIR          = "tmp/blenderconfig/"
LARGE_BLENDER_FILE_MB = 650        # kept for parity (not used here)

# ─────────────────────────── public API ────────────────────────────
async def build_scene(data: PostData, scene_id: str) -> Path:
    """
    Faithful port of RunBlenderScripts.Run() up to—but not including—the
    cloud-render submission.  Returns the prepared *.blend path.
    """
    # 1) working root mirrors C# →  /tmp/<scene_id>/
    root = Path(tempfile.gettempdir()) / str(scene_id)
    _mkdirs(root)

    blend_out = root / TEMP_BFILE_TEMPLATE.format(scene_id)

    # 2) core downloads ---------------------------------------------------------
    scene_gltf  = await _dl_scene_gltf(root / TEMP_SCENE_DIR,
                                       data.scene_gltf_uri, data.space_image_id)
    scene_image = await _dl_scene_image(root / TEMP_SCENE_DIR,
                                        data.space_image_uri, data.space_image_id)
    model_paths = await _dl_all_models(root / TEMP_MODELS_DIR, data.scene_objects)

    (scene_script, default_scene, mirror_script, user_mirror_script,
     tools_error) = await _dl_blender_tools(root / TEMP_SCENE_DIR, data.is360)

    cfg_path = _write_blender_cfg(root / TEMP_CFG_DIR, blend_out,
                                  scene_gltf, scene_image,
                                  data, model_paths)

    # 3) Blender command pipeline ----------------------------------------------
    blender = Path(settings.blender_exe_location)
    if not blender.exists():
        raise FileNotFoundError(f"Blender not found at {blender}")

    _run(f"/local/scripts/defualt.blend -b -P /local/scripts/ApplyDesignSceneScript.py -- -i {cfg_path}"
         if tools_error else
         f"{default_scene} -b -P {scene_script} -- -i {cfg_path}")

    if data.mirror_in_scene:
        _run(f"{blend_out} -b -P {mirror_script}")

    if data.rendering_preset and data.rendering_preset.is_extension:
        ext = await _dl_extension(root / TEMP_SCENE_DIR,
                                  data.rendering_preset.script_download_url)
        if ext:
            _run(f"{blend_out} -b -P {ext}")

    has_object_mirrors = any(o.is_mirror for o in data.scene_objects)
    if has_object_mirrors and not data.mirror_in_scene and not data.is360:
        _run(f"{blend_out} -b -P {user_mirror_script}")

    return blend_out

# ─────────────────────────── helpers ────────────────────────────
def _mkdirs(root: Path):
    for sub in (TEMP_SCENE_DIR, TEMP_MODELS_DIR, TEMP_BFILE_DIR, TEMP_CFG_DIR):
        (root / sub).mkdir(parents=True, exist_ok=True)

async def _fetch(url: str, dest: Path, text: bool = False):
    async with aiohttp.ClientSession() as s, s.get(url) as r:
        r.raise_for_status()
        data = await (r.text() if text else r.read())
        dest.parent.mkdir(parents=True, exist_ok=True)
        mode = "w" if text else "wb"
        with open(dest, mode) as f:
            f.write(data)

async def _dl_scene_gltf(dir_: Path, uri: str, sid: int) -> Path:
    p = dir_ / f"scene{sid}.gltf"
    await _fetch(uri, p)
    return p

async def _dl_scene_image(dir_: Path, uri: str, sid: int) -> Path:
    p = dir_ / f"scene{sid}{Path(uri).suffix}"
    await _fetch(uri, p)
    return p

async def _dl_all_models(dir_: Path, objs: List[SceneObjectData]) -> List[str]:
    tasks, dests = [], []
    for o in objs:
        d = dir_ / f"{o.name}.blend"
        tasks.append(_fetch(o.model_blender_uri, d))
        dests.append(str(d))
    await asyncio.gather(*tasks)
    return dests

async def _dl_blender_tools(dir_: Path, is360: bool) -> Tuple[str,str,str,str,bool]:
    try:
        scene_script_url = (settings.url_blender_360_scene_script
                            if is360 else settings.url_blender_scene_script)
        scene_file_url   = (settings.url_blender_360_scene_file
                            if is360 else settings.url_blender_scene_file)

        scene_script  = dir_ / "ApplyDesignSceneScript.py"
        mirror_script = dir_ / "ApplyDesignSceneMirrorScript.py"
        user_mirror   = dir_ / "ApplyDesignUserMirrorScript.py"
        default_scene = dir_ / "Default.blend"

        await asyncio.gather(
            _fetch(scene_script_url,          scene_script,  text=True),
            _fetch(settings.url_blender_mirror_script,       mirror_script, text=True),
            _fetch(settings.url_blender_user_mirror_script,  user_mirror,   text=True),
            _fetch(scene_file_url,            default_scene)
        )
        return map(str, (scene_script, default_scene,
                         mirror_script, user_mirror)) | (False,)   # type: ignore
    except Exception as e:
        logger.error("Blender-tool download failed → fallback: %s", e, exc_info=True)
        return ("", "", "", "", True)

async def _dl_extension(dir_: Path, url: str | None) -> str | None:
    if not url:
        return None
    dest = dir_ / "ApplyDesignExtensionSceneScript.py"
    try:
        await _fetch(url, dest, text=True)
        return str(dest)
    except Exception:
        return None

def _write_blender_cfg(cfg_dir: Path, blend_out: Path,
                       scene_path: Path, image_path: Path,
                       data: PostData, model_paths: List[str]) -> Path:
    cfg_dir.mkdir(parents=True, exist_ok=True)
    models = []
    for i, o in enumerate(data.scene_objects):
        models.append({
            "ModelBlenderPath":      model_paths[i],
            "InnerPath":             o.inner_path,
            "ObjectName":            o.object_name,
            "PositionX":             o.position_x,  "PositionY": o.position_y,  "PositionZ": o.position_z,
            "RotationX":             o.rotation_x,  "RotationY": o.rotation_y,  "RotationZ": o.rotation_z,
            "QuaternionX":           o.quaternion_x,"QuaternionY":o.quaternion_y,
            "QuaternionZ":           o.quaternion_z,"QuaternionW":o.quaternion_w,
            "Scale":                 o.scale,       "ScaleX": o.scale_x, "ScaleY": o.scale_y, "ScaleZ": o.scale_z,
            "IsCurtain": o.is_curtain, "IsFloor": o.is_floor, "ShowLights": o.show_lights,
            "LightsColor": o.lights_color, "LightsPower": o.lights_power,
            "LightRadius": o.light_radius,
            "LightSourcesPositions": [v.model_dump(mode="python") for v in (o.light_sources_positions or [])],
            "IsMirror": o.is_mirror
        })

    cfg = {
        "SceneGLTFPath": str(scene_path),
        "Samples": data.samples,
        "OutputFormat": data.output_format,
        "ResX": data.res_x, "ResY": data.res_y,
        "SceneImagePath": str(image_path),
        "SceneModels": models,
        "SceneScale": data.scene_scale,
        "SceneObjectName": data.scene_object_name,
        "CameraObjectName": data.camera_object_name,
        "FrameObjectName": "ApplyDesignGroup",
        "SceneMatName": "Scene_Material",
        "SceneSaveLocation": str(blend_out),
        "AreaLightObjectName": "Area Light Source",
        "PointLightObjectName": "Point Light Source",
        "AmbientLightObjectName": "Ambient Light",
        "AreaLightMatName": "Plane_Emission_Mat",
        "MirrorInScene": data.mirror_in_scene
    }
    cfg_path = cfg_dir / "config.json"
    cfg_path.write_text(json.dumps(cfg))
    return cfg_path

def _run(cmd: str):
    full = [settings.blender_exe_location] + cmd.split()
    logger.info("▶  %s", " ".join(full))
    proc = subprocess.run(full, capture_output=True, text=True)
    logger.info(proc.stdout)
    if proc.returncode:
        logger.error(proc.stderr)
        raise RuntimeError(f"Blender exited {proc.returncode}")
