from __future__ import annotations
from typing import List, Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
#  Vector helper
# ──────────────────────────────────────────────────────────────────────────────
class SimpleVector3(BaseModel):
    x: float = Field(alias="X")
    y: float = Field(alias="Y")
    z: float = Field(alias="Z")

    model_config = {"populate_by_name": True}


# ──────────────────────────────────────────────────────────────────────────────
#  Scene objects
# ──────────────────────────────────────────────────────────────────────────────
class SceneObjectData(BaseModel):
    name:               str   = Field(alias="Name")
    model_blender_uri:  str   = Field(alias="ModelBlenderUri")
    inner_path:         str | None = Field(alias="InnerPath", default=None)

    object_name:        str | None = Field(alias="ObjectName",        default=None)
    camera_object_name: str | None = Field(alias="CameraObjectName",  default=None)

    position_x: float   = Field(alias="PositionX")
    position_y: float   = Field(alias="PositionY")
    position_z: float   = Field(alias="PositionZ")

    rotation_x: float   = Field(alias="RotationX")
    rotation_y: float   = Field(alias="RotationY")
    rotation_z: float   = Field(alias="RotationZ")

    quaternion_x: float = Field(alias="QuaternionX")
    quaternion_y: float = Field(alias="QuaternionY")
    quaternion_z: float = Field(alias="QuaternionZ")
    quaternion_w: float = Field(alias="QuaternionW")

    # scale – legacy single + per-axis
    scale:   float = Field(alias="Scale",  default=1.0)
    scale_x: float = Field(alias="ScaleX", default=1.0)
    scale_y: float = Field(alias="ScaleY", default=1.0)
    scale_z: float = Field(alias="ScaleZ", default=1.0)

    groups:        list[str]          = Field(alias="Groups", default_factory=list)
    is_floor:      bool              = Field(alias="IsFloor",   default=False)
    is_curtain:    bool              = Field(alias="IsCurtain", default=False)
    is_mirror:     bool              = Field(alias="IsMirror",  default=False)

    show_lights:   bool              = Field(alias="ShowLights", default=False)
    lights_color:  str | None        = Field(alias="LightsColor", default=None)
    lights_power:  float | None      = Field(alias="LightsPower", default=None)
    light_radius:  float | None      = Field(alias="LightRadius", default=None)

    light_sources_positions: list[SimpleVector3] | None = Field(
        alias="LightSourcesPositions", default=None
    )

    model_config = {"populate_by_name": True}


# ──────────────────────────────────────────────────────────────────────────────
#  Render preset
# ──────────────────────────────────────────────────────────────────────────────
class RenderPresetData(BaseModel):
    render_preset_name: str  = Field(alias="RenderPresetName")
    is_extension:       bool = Field(alias="IsExtension", default=False)
    script_download_url: str | None = Field(alias="ScriptDownloadURL", default=None)

    model_config = {"populate_by_name": True}


# ──────────────────────────────────────────────────────────────────────────────
#  Main POST payload
# ──────────────────────────────────────────────────────────────────────────────
class PostData(BaseModel):
    scene_objects:      List[SceneObjectData] = Field(alias="SceneObjects")
    render_job_id:      int   = Field(alias="RenderJobID")
    space_image_id:     int   = Field(alias="SpaceImageID")

    scene_gltf_uri:     str   = Field(alias="SceneGLTFUri")
    scene_scale:        float = Field(alias="SceneScale", default=1.0)

    res_x:              float = Field(alias="ResX", default=1920)
    res_y:              float = Field(alias="ResY", default=1080)

    samples:            int   = Field(alias="Samples", default=256)
    space_image_uri:    str   = Field(alias="SpaceImageUri")

    scene_mat_name:     str | None = Field(alias="SceneMatName", default=None)
    output_format:      str        = Field(alias="OutputFormat",  default="PNG")

    scene_object_name:  str | None = Field(alias="SceneObjectName",  default=None)
    camera_object_name: str        = Field(alias="CameraObjectName", default="Prod")

    mirror_in_scene:    bool  = Field(alias="MirrorInScene", default=False)
    is360:              bool  = Field(alias="Is360",         default=False)

    rendering_preset:   RenderPresetData | None = Field(alias="RenderingPreset", default=None)

    # extra convenience for Cloud Run – not present in C# but harmless if omitted
    webhook:            str | None = Field(default=None)

    model_config = {"populate_by_name": True}
