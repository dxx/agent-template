import httpx
from typing import Any


async def request(
    method: str,
    url: str,
    *,
    params: dict | None = None,
    json: dict | None = None,
    **kwargs,
) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        return await client.request(method, url, params=params, json=json, **kwargs)


async def get(url: str, *, params: dict | None = None, **kwargs) -> httpx.Response:
    return await request("GET", url, params=params, **kwargs)


async def post(
    url: str, *, params: dict | None = None, json: dict | None = None, **kwargs
) -> httpx.Response:
    return await request("POST", url, params=params, json=json, **kwargs)


async def get_json(url: str, *, params: dict | None = None, **kwargs) -> Any:
    resp = await get(url, params=params, **kwargs)
    return resp.json()


async def post_json(
    url: str, *, params: dict | None = None, json: dict | None = None, **kwargs
) -> Any:
    resp = await post(url, params=params, json=json, **kwargs)
    return resp.json()
