FROM python:3.11-slim

RUN apt-get update && apt-get install -y gcc g++ wget xz-utils && rm -rf /var/lib/apt/lists/*

# download Blender just like earlier
RUN cd /tmp && wget -q https://download.blender.org/release/Blender3.5/blender-3.5.0-linux-x64.tar.xz \
    && tar xf blender-3.5.0-linux-x64.tar.xz -C /usr/bin/ \
    && rm blender-3.5.0-linux-x64.tar.xz \
    && ln -s /usr/bin/blender-3.5.0-linux-x64/blender /usr/local/bin/blender

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
