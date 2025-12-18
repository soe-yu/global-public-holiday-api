from fastapi import FastAPI, HTTPException, Query
import httpx
import os
import json

app = FastAPI(title="グローバル祝日・祭りAPI")

# simple in-memory cache to avoid repeated external calls during development
holidays_cache = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FESTIVAL_DIR = os.path.join(BASE_DIR, "festivals")

@app.get("/")
async def home():
    return {"message": "APIが起動しています。/holidays または /festivals をご利用ください。"}

@app.get("/holidays")
async def get_holidays(
    country: str = Query(..., min_length=2, max_length=2, description="国コード (例: JP)"),
    year: int = Query(..., ge=1900, le=2100, description="年 (例: 2025)")
):
    key = (country.upper(), year)

    if key in holidays_cache:
        return {"source": "cache", "data": holidays_cache[key]}

    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country.upper()}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)

    if resp.status_code != 200:
        raise HTTPException(status_code=404, detail="祝日データが見つかりません。国コードまたは年を確認してください。")

    data = resp.json()
    holidays_cache[key] = data
    return {"source": "nager.date", "data": data}

@app.get("/festivals")
async def get_festivals(
    country: str = Query(..., min_length=2, max_length=2, description="国コード (例: JP)")
):
    filename = f"{country.upper()}.json"
    filepath = os.path.join(FESTIVAL_DIR, filename)

    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="祭りデータが見つかりません。国コードを確認してください。")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail="祭りデータの読み込みに失敗しました。")

    return {"source": "local", "data": data}

# -----------------------------
# FESTIVALS TEST ENDPOINT
# -----------------------------
@app.get("/festivals/test")
def test_festivals():
    import os
    files = os.listdir(FESTIVAL_DIR)
    return {"festivals_dir": FESTIVAL_DIR, "files": files}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
