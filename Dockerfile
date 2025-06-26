########################################################################
#  ApplyDesign Render API  –  single-stage image with Blender 3.5
#
#  • Python 3.11-slim base
#  • Installs system libs required by Blender (same list as legacy C# image)
#  • Downloads & unpacks Blender 3.5.0
#  • Installs Python deps from requirements.txt
#  • Exposes FastAPI on :8080
########################################################################

FROM python:3.11-slim AS runtime

# ---------------- system packages ----------------
# build helpers (wget, gcc) first;  then all runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget gcc g++ xz-utils \
        libx11-6 libxxf86vm1 libxfixes3 libxi6 libxrender1 \
        libxkbcommon0 libxkbcommon-x11-0 libgl1-mesa-glx libfreetype6 \
        libopengl0 libgomp1 libsm6 libice6 libxext6 libxt6 libxmu6 \
        libglu1-mesa libfontconfig1 libxinerama1 libxrandr2 libxcursor1 \
        libjpeg62-turbo libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# ---------------- Blender 3.5 ----------------
ENV BLENDER_VER=3.5.0
RUN wget -q https://download.blender.org/release/Blender${BLENDER_VER%.*}/blender-${BLENDER_VER}-linux-x64.tar.xz \
    && tar -xf blender-${BLENDER_VER}-linux-x64.tar.xz -C /usr/local \
    && rm blender-${BLENDER_VER}-linux-x64.tar.xz \
    && ln -s /usr/local/blender-${BLENDER_VER}-linux-x64/blender /usr/local/bin/blender \
    && cp /usr/local/blender-${BLENDER_VER}-linux-x64/lib/lib* /usr/local/lib/ && ldconfig

# ---------------- Python deps ----------------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------- project code ----------------
COPY . .

# ---------------- env & entry -----------------
ENV BLENDER_USER_CONFIG=/tmp/.config/blender \
    BLENDER_USER_SCRIPTS=/tmp/.config/blender/scripts \
    DISPLAY=:99 \
    PORT=8080

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
