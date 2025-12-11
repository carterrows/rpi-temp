"""
/api/temp is stateless and only invokes vcgencmd when the web UI polls it,
so no temperature commands run when nobody is connected.
"""
from typing import Optional
import subprocess

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

templates = Jinja2Templates(directory="templates")
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/temp", response_class=JSONResponse)
async def read_temperature() -> JSONResponse:
    try:
        output = subprocess.check_output(
            ["vcgencmd", "measure_temp"],
            text=True,
        ).strip()
    except FileNotFoundError as exc:
        return JSONResponse(
            status_code=500,
            content={"error": "vcgencmd not found", "details": str(exc)},
        )
    except subprocess.CalledProcessError as exc:
        return JSONResponse(
            status_code=500,
            content={"error": "vcgencmd failed", "details": str(exc)},
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        return JSONResponse(
            status_code=500,
            content={"error": "Unexpected error", "details": str(exc)},
        )

    temp_c: Optional[float] = None
    if output.startswith("temp="):
        value_part = output.split("=", 1)[1].strip()
        if value_part.endswith("'C"):
            value_part = value_part[:-2]
        try:
            temp_c = float(value_part)
        except ValueError:
            temp_c = None

    return JSONResponse(content={"temp_c": temp_c, "raw": output})
