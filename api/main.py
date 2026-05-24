from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import httpx
from datetime import datetime
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

STOCK_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQ6oDlhxWgtYn3IVCV1-ewP6kMsULRuVJPXiAYLMV_dXVXRbH8VGI7LzM6wtXqXX9EJTxQgFKqb0BlF"
    "/pub?gid=756201628&single=true&output=csv"
)

BANK_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQ6oDlhxWgtYn3IVCV1-ewP6kMsULRuVJPXiAYLMV_dXVXRbH8VGI7LzM6wtXqXX9EJTxQgFKqb0BlF"
    "/pub?gid=983098033&single=true&output=csv"
)

STOCK_DIR = Path("/app/data/stock")
BANK_DIR  = Path("/app/data/bank")


async def _fetch_sheet(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"無法抓取 Google Sheets：{e}")
    return resp.text


def _snapshot_response(data_dir: Path, prefix: str, force: bool, sheet_url: str):
    date_str = datetime.now().strftime("%Y-%m-%d")
    snapshot = data_dir / f"{prefix}_{date_str}.csv"
    return date_str, snapshot


@app.get("/api/stock/refresh", response_class=PlainTextResponse)
async def refresh_stock(force: bool = False):
    """回傳股票 CSV。今日快照存在時直接回傳；否則從 Google Sheets 抓取並存檔。"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    snapshot = STOCK_DIR / f"stock_{date_str}.csv"

    if not force and snapshot.exists():
        return PlainTextResponse(
            snapshot.read_text(encoding="utf-8"),
            headers={"X-Data-Source": "cache", "X-Snapshot-Date": date_str},
        )

    csv_content = await _fetch_sheet(STOCK_SHEET_URL)
    STOCK_DIR.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(csv_content, encoding="utf-8")

    return PlainTextResponse(
        csv_content,
        headers={"X-Data-Source": "fresh", "X-Snapshot-Date": date_str},
    )


@app.get("/api/stock/history")
async def list_stock_history():
    """列出所有股票歷史快照檔名。"""
    return [f.name for f in sorted(STOCK_DIR.glob("stock_*.csv"))]


@app.get("/api/bank/refresh", response_class=PlainTextResponse)
async def refresh_bank(force: bool = False):
    """回傳銀行現金 CSV。今日快照存在時直接回傳；否則從 Google Sheets 抓取並存檔。"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    snapshot = BANK_DIR / f"bank_{date_str}.csv"

    if not force and snapshot.exists():
        return PlainTextResponse(
            snapshot.read_text(encoding="utf-8"),
            headers={"X-Data-Source": "cache", "X-Snapshot-Date": date_str},
        )

    csv_content = await _fetch_sheet(BANK_SHEET_URL)
    BANK_DIR.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(csv_content, encoding="utf-8")

    return PlainTextResponse(
        csv_content,
        headers={"X-Data-Source": "fresh", "X-Snapshot-Date": date_str},
    )


@app.get("/api/bank/history")
async def list_bank_history():
    """列出所有銀行歷史快照檔名。"""
    return [f.name for f in sorted(BANK_DIR.glob("bank_*.csv"))]
