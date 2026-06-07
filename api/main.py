from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import csv
import io
import httpx
from datetime import datetime
from pathlib import Path
from typing import Dict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "PATCH"],
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

LABOR_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQ6oDlhxWgtYn3IVCV1-ewP6kMsULRuVJPXiAYLMV_dXVXRbH8VGI7LzM6wtXqXX9EJTxQgFKqb0BlF"
    "/pub?gid=889457991&single=true&output=csv"
)

STOCK_DIR   = Path("/app/data/stock")
BANK_DIR    = Path("/app/data/bank")
PENSION_DIR = Path("/app/data/pension")


async def _fetch_sheet(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"無法抓取 Google Sheets：{e}")
    return resp.text


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


@app.patch("/api/stock/snapshot")
async def patch_stock_snapshot(prices: Dict[str, float] = Body(...)):
    """Finnhub 取得的即時股價寫回今日快照，只更新 Current Price 為 '-' 的列。"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    snapshot = STOCK_DIR / f"stock_{date_str}.csv"
    if not snapshot.exists():
        raise HTTPException(status_code=404, detail="今日快照不存在")

    content = snapshot.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    fieldnames = list(reader.fieldnames)

    updated = 0
    for row in rows:
        ticker = row.get("Ticker", "")
        if ticker in prices and row.get("Current Price", "").strip() == "-":
            row["Current Price"] = str(round(prices[ticker], 4))
            updated += 1

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    snapshot.write_text(output.getvalue(), encoding="utf-8")

    return {"updated": updated}


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


@app.get("/api/pension/refresh", response_class=PlainTextResponse)
async def refresh_pension(force: bool = False):
    """回傳勞退 CSV。今日快照存在時直接回傳；否則從 Google Sheets 抓取並存檔。"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    snapshot = PENSION_DIR / f"pension_{date_str}.csv"

    if not force and snapshot.exists():
        return PlainTextResponse(
            snapshot.read_text(encoding="utf-8"),
            headers={"X-Data-Source": "cache", "X-Snapshot-Date": date_str},
        )

    csv_content = await _fetch_sheet(LABOR_SHEET_URL)
    PENSION_DIR.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(csv_content, encoding="utf-8")

    return PlainTextResponse(
        csv_content,
        headers={"X-Data-Source": "fresh", "X-Snapshot-Date": date_str},
    )


@app.get("/api/pension/history")
async def list_pension_history():
    """列出所有勞退歷史快照檔名。"""
    return [f.name for f in sorted(PENSION_DIR.glob("pension_*.csv"))]
