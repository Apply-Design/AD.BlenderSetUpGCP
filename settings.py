from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ───────── Cloud / infra ─────────────────────────
    project_id: str = "applydesign"
    region: str = "us-central1"
    bucket: str = "applydesign-results"

    # ───────── Blender asset URLs (from App-Config / env) ─────────
    url_blender_scene_script:           str = "https://applydesign.blob.core.windows.net/blender-function-tools/Blender35/SceneScript.py"
    url_blender_360_scene_script:       str = "https://applydesign.blob.core.windows.net/blender-function-tools/Blender35/SceneScript360.py"
    url_blender_scene_file:             str = "https://applydesign.blob.core.windows.net/blender-function-tools/Blender35/Base.blend"
    url_blender_360_scene_file:         str = "https://applydesign.blob.core.windows.net/blender-function-tools/Blender35/Base360.blend"
    url_blender_mirror_script:          str = "https://applydesign.blob.core.windows.net/blender-function-tools/Blender35/SceneMirrorScript.py"
    url_blender_user_mirror_script:     str = "https://applydesign.blob.core.windows.net/blender-function-tools/Blender35/UserMirrorScript.py"
    blender_exe_location:               str = "/usr/local/bin/blender"

    class Config:
        env_file = ".env"

settings = Settings()               # import-safe singleton
