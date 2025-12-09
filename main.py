from fastapi import FastAPI, HTTPException, Query
import httpx

app = FastAPI(title="Global Public Holidays API")

# simple in-memory cache to avoid repeated external calls during development
holidays_cache = {}

@app.get("/")
async def home():
    return {"message": "Global Public Holidays API Running"}

@app.get("/holidays")
async def get_holidays(country: str = Query(..., min_length=2, max_length=2),
                       year: int = Query(..., ge=1900, le=2100)):
    """
    Example: /holidays?country=jp&year=2025
    country must be 2-letter ISO code (JP, US, GB, etc.)
    """
    key = (country.upper(), year)

    # return cached data if available
    if key in holidays_cache:
        return {"source": "cache", "data": holidays_cache[key]}

    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country.upper()}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)

    if resp.status_code != 200:
        # external API returned error: forward a clean message
        raise HTTPException(status_code=404, detail="Holidays not found. Check country code/year.")

    data = resp.json()
    holidays_cache[key] = data  # store in memory cache
    return {"source": "nager.date", "data": data}
