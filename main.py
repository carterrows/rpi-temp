"""
/api/stats is stateless and only invokes vcgencmd or reads fan RPM when the web
UI polls it, so no hardware reads run when nobody is connected.
"""
from pathlib import Path
from typing import Optional, Tuple
import subprocess
import glob

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

templates = Jinja2Templates(directory="templates")
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

FAN_MAX_RPM = 8000
FAN_GLOB = "/sys/devices/platform/cooling_fan/hwmon/hwmon*/fan1_input"


def read_cpu_temp() -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """Read CPU temp via vcgencmd; return (temp_c, raw_output, error)."""
    try:
        output = subprocess.check_output(
            ["vcgencmd", "measure_temp"],
            text=True,
        ).strip()
    except FileNotFoundError as exc:
        return None, None, f"vcgencmd not found: {exc}"
    except subprocess.CalledProcessError as exc:
        return None, None, f"vcgencmd failed: {exc}"
    except Exception as exc:  # pragma: no cover - defensive fallback
        return None, None, f"Unexpected error: {exc}"

    temp_c: Optional[float] = None
    if output.startswith("temp="):
        value_part = output.split("=", 1)[1].strip()
        if value_part.endswith("'C"):
            value_part = value_part[:-2]
        try:
            temp_c = float(value_part)
        except ValueError:
            temp_c = None

    return temp_c, output, None


def find_fan_input_path() -> Optional[Path]:
    """Locate the cooling fan rpm file, resilient to hwmon index changes."""
    for match in sorted(glob.glob(FAN_GLOB)):
        path = Path(match)
        if path.is_file():
            return path
    return None


def read_fan_rpm() -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """Read fan RPM from sysfs; return (rpm, path_used, error)."""
    path = find_fan_input_path()
    if not path:
        return None, None, "Fan rpm file not found"

    try:
        content = path.read_text(encoding="utf-8").strip()
    except Exception as exc:  # pragma: no cover - defensive fallback
        return None, str(path), f"Failed to read fan rpm: {exc}"

    try:
        rpm = int(content)
    except ValueError:
        return None, str(path), f"Invalid rpm value: {content!r}"

    return rpm, str(path), None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/stats", response_class=JSONResponse)
async def read_stats() -> JSONResponse:
    temp_c, temp_raw, temp_error = read_cpu_temp()
    fan_rpm, fan_path, fan_error = read_fan_rpm()

    fan_percent: Optional[float] = None
    if fan_rpm is not None and FAN_MAX_RPM > 0:
        fan_percent = round((fan_rpm / FAN_MAX_RPM) * 100, 1)

    return JSONResponse(
        content={
            "temp_c": temp_c,
            "temp_raw": temp_raw,
            "temp_error": temp_error,
            "fan_rpm": fan_rpm,
            "fan_percent": fan_percent,
            "fan_path": fan_path,
            "fan_error": fan_error,
        }
    )
