"""FastAPI app — Tennis de Table stats."""

import base64
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import json
from fastapi import Request
from scraping.client import FFTTClient
from scraping.social import generate_poster, filter_by_match_day
from scraping.stats import analyze_home_away_performance
from scraping.plot import (
    plot_home_away_performance,
    plot_player_participations_by_phase,
    plot_team_match_matrix,
    plot_team_series,
)
from scraping.report import build_excel_report

app = FastAPI(title="TT Stats API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


COUNTER_FILE = Path("visitors.json")


def _load_visitors():
    if COUNTER_FILE.exists():
        return json.loads(COUNTER_FILE.read_text())
    return {"count": 0, "ips": []}


def _save_visitors(data):
    COUNTER_FILE.write_text(json.dumps(data))


@app.middleware("http")
async def count_visitors(request: Request, call_next):
    ip = (
        request.headers.get("x-forwarded-for", request.client.host)
        .split(",")[0]
        .strip()
    )
    data = _load_visitors()
    if ip not in data["ips"]:
        data["ips"].append(ip)
        data["count"] += 1
        _save_visitors(data)
    return await call_next(request)


@app.get("/visitors")
def get_visitors():
    data = _load_visitors()
    print(data)
    return {"unique_visitors": data["count"]}


# Load clubs mapping from shared JSON file (app/src/clubs.json)
ROOT = Path(__file__).resolve().parents[2]
CLUBS_FILE = ROOT / "app" / "src" / "clubs.json"
if CLUBS_FILE.exists():
    try:
        CLUBS = json.loads(CLUBS_FILE.read_text())
    except Exception:
        CLUBS = {}
else:
    CLUBS = {}

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

app.mount("/files", StaticFiles(directory=str(OUTPUT_DIR)), name="files")


class AnalyzeRequest(BaseModel):
    club_id: str


class SocialRequest(BaseModel):
    club_id: str
    phase_index: int
    match_index: int


def _fig_to_base64(path: Path) -> str:
    """Reads a file and returns it encoded in base64."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


@app.get("/clubs")
def list_clubs():
    """Returns the list of available clubs."""
    return [{"id": cid, "name": name} for cid, name in CLUBS.items()]


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """
    Fetches the data for a club, generates plots and an Excel report.

    Returns:
    - 4 images encoded in base64 (JPG)
    - the URL of the downloadable Excel file
    """
    club_id = req.club_id
    club_name = CLUBS[club_id]

    try:
        client = FFTTClient(config_path=None)
        matches_df, simples_df, doubles_df = client.scrape_club(club_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur API fédération : {e}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        p_home_away = tmp / "home_away.jpg"
        p_participations = tmp / "participations.jpg"
        p_series = tmp / "series.jpg"
        p_matrix = tmp / "matrix.jpg"
        if len(simples_df) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Pas de matches enregistrés pour le club : {club_name}",
            )
        try:
            home_away_df = analyze_home_away_performance(simples_df)
            plot_home_away_performance(home_away_df, save_path=p_home_away)
            plot_player_participations_by_phase(simples_df, save_path=p_participations)
            plot_team_series(matches_df, save_path=p_series)
            plot_team_match_matrix(matches_df, save_path=p_matrix)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Erreur génération plots : {e}"
            )

        # --- Excel (stored in outputs/ for download) ---
        safe_name = club_name.lower().replace(" ", "_").replace("/", "_")[:40]
        excel_path = OUTPUT_DIR / f"{safe_name}.xlsx"

        try:
            build_excel_report(
                matches_df, simples_df, doubles_df, output_path=str(excel_path)
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Erreur génération Excel : {e}"
            )

        # --- base64 encoding of images ---
        return {
            "club_id": club_id,
            "club_name": club_name,
            "plot_home_away": _fig_to_base64(p_home_away),
            "plot_participations": _fig_to_base64(p_participations),
            "plot_series": _fig_to_base64(p_series),
            "plot_matrix": _fig_to_base64(p_matrix),
            "excel_url": f"/files/{excel_path.name}",
        }


@app.get("/files/{filename}")
def download_excel(filename: str):
    """Direct download of the Excel file."""
    path = OUTPUT_DIR / filename
    if not path.exists() or path.suffix != ".xlsx":
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )


@app.post("/social/")
def generate_social_poster(req: SocialRequest):
    """Generate a social media poster for a specific match."""

    club_id = req.club_id
    club_name = CLUBS[club_id]

    try:
        client = FFTTClient(config_path=None)
        matches_df, simples_df, doubles_df = client.scrape_club(club_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur API fédération : {e}")
    # try:

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        day_matchs = filter_by_match_day(matches_df, req.match_index, req.phase_index)
        generate_poster(
            matchs=day_matchs,
            match_index=req.match_index,
            phase_index=req.phase_index,
            output=tmp / "poster.svg",
            export_png=True,
        )
        return {
            "club_id": club_id,
            "club_name": club_name,
            "plot_social": _fig_to_base64(tmp / "poster.png"),
        }

    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Erreur génération poster social : {e}")
