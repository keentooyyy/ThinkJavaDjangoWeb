from django.http import JsonResponse
import aiohttp

BASE_URL = "https://psgc.cloud/api/v2"

async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            res.raise_for_status()
            return await res.json()

async def provinces(request):
    region_code = request.GET.get("region")
    if not region_code:
        return JsonResponse({"error": "Missing region"}, status=400)

    data = await fetch_json(f"{BASE_URL}/provinces?region_code={region_code}")
    return JsonResponse(data["data"], safe=False)

async def cities(request):
    prov_code = request.GET.get("province_code")
    if not prov_code:
        return JsonResponse({"error": "Missing province_code"}, status=400)

    data = await fetch_json(f"{BASE_URL}/provinces/{prov_code}/cities-municipalities")
    return JsonResponse(data["data"], safe=False)

async def barangays(request):
    city_code = request.GET.get("city_code")
    if not city_code:
        return JsonResponse({"error": "Missing city_code"}, status=400)

    data = await fetch_json(f"{BASE_URL}/cities-municipalities/{city_code}/barangays")
    return JsonResponse(data["data"], safe=False)