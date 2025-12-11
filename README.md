# Raspberry Pi CPU Temperature Monitor

Minimal FastAPI + Tailwind web UI that shows live CPU temperature on a Raspberry Pi. The backend only runs `vcgencmd measure_temp` when the page polls it, so no temperature commands run when nobody is viewing the site.

## Requirements
- Raspberry Pi OS with `vcgencmd` available (usually `/usr/bin/vcgencmd`)
- Docker and Docker Compose

## Run with Docker Compose
```sh
docker compose build
docker compose up -d
```
Then open `http://<raspberry-pi-ip>:9000/` in your browser.

### Notes on device/binary mounts
- `docker-compose.yml` bind-mounts `/usr/bin/vcgencmd` into the container (read-only) and exposes `/dev/vchiq`.
- If `which vcgencmd` reports a different path on your Pi, adjust the volume in `docker-compose.yml`.
- If you hit permission issues, you can try uncommenting `privileged: true` in `docker-compose.yml` (not recommended unless necessary).

## Project structure
- `main.py` — FastAPI app with `/` (HTML) and `/api/temp` (JSON).
- `templates/index.html` — Tailwind CDN UI with 1s polling, starts/stops on focus/blur.
- `requirements.txt` — Python deps (fastapi, uvicorn, jinja2).
- `Dockerfile`, `docker-compose.yml` — Container build/run setup for Pi.

## Local (non-Docker) run
```sh
python -m venv .venv
source .venv/bin/activate    # on Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 9000
```
Visit `http://localhost:9000/`.
