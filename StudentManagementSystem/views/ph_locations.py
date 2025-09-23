import aiohttp
from django.http import JsonResponse

BASE_URL_V2 = "https://psgc.cloud/api/v2"
BASE_URL_V1 = "https://psgc.cloud/api"   # ✅ v1 for NCR cities

def fix_encoding(text: str) -> str:
    """Fix common encoding issues from PSGC API."""
    if not isinstance(text, str):
        return text
    return text.replace("Ã±", "ñ")

def normalize_data(data):
    """Recursively fix all strings in dict/list."""
    if isinstance(data, dict):
        return {k: normalize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [normalize_data(item) for item in data]
    elif isinstance(data, str):
        return fix_encoding(data)
    return data

async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            res.raise_for_status()
            raw = await res.json()
            return normalize_data(raw)

# ----------------- Views -----------------

async def provinces(request):
    region_code = request.GET.get("region")
    if not region_code:
        return JsonResponse({"error": "Missing region"}, status=400)

    data = await fetch_json(f"{BASE_URL_V2}/provinces?region_code={region_code}")
    provinces = data["data"]

    # ✅ Always append Metro Manila (NCR)
    provinces.append({
        "code": "NCR",
        "name": "Metro Manila",
        "region": "National Capital Region (NCR)"
    })

    return JsonResponse(provinces, safe=False)

async def cities(request):
    prov_code = request.GET.get("province_code")
    if not prov_code:
        return JsonResponse({"error": "Missing province_code"}, status=400)

    if prov_code == "NCR":
        # ✅ NCR → use v1 endpoint directly
        data = await fetch_json(f"{BASE_URL_V1}/regions/1300000000/cities")
        return JsonResponse(data, safe=False)
    else:
        data = await fetch_json(f"{BASE_URL_V2}/provinces/{prov_code}/cities-municipalities")
        return JsonResponse(data["data"], safe=False)

async def barangays(request):
    city_code = request.GET.get("city_code")
    if not city_code:
        return JsonResponse({"error": "Missing city_code"}, status=400)

    # Special case: City of Manila (1380600000)
    if city_code == "1380600000":
        districts = [
            "Binondo",
            "Ermita",
            "Intramuros",
            "Malate",
            "Paco (Dilao)",
            "Pandacan",
            "Port Area",
            "Quiapo",
            "Sampaloc",
            "San Miguel",
            "San Nicolas",
            "Santa Ana",
            "Santa Cruz",
            "Tondo",
        ]
        data = [{"name": d, "type": "District"} for d in districts]
        return JsonResponse(data, safe=False)

    # Default: fetch barangays from PSGC
    data = await fetch_json(f"{BASE_URL_V2}/cities-municipalities/{city_code}/barangays")
    return JsonResponse(data["data"], safe=False)
