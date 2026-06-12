from __future__ import annotations

import uvicorn
import json

import httpx
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import PlainTextResponse, Response

from settings import xsettings

app = FastAPI(title="WhatsApp Webhook Router")

WEBHOOK_VERIFY_TOKEN = xsettings.WEBHOOK_VERIFY_TOKEN

#supporting functions

def get_value(payload: dict) -> dict:
    """Return ``entry[0].changes[0].value`` from a webhook payload, or ``{}``."""
    try:
        return payload["entry"][0]["changes"][0]["value"] or {}
    except (KeyError, IndexError, TypeError):
        return {}


def get_phone_number_id(payload: dict) -> str:
    """Return the receiving number's ``phone_number_id`` (stripped), or ``""``."""
    return get_value(payload).get("metadata", {}).get("phone_number_id", "").strip()


def get_first_message(payload: dict) -> dict:
    """Return the first message object in the payload, or ``{}`` if there is none."""
    messages = get_value(payload).get("messages") or []
    return messages[0] if messages else {}


# ── Phone-number → downstream service routing ─────────────────────────────────
PHONE_TO_SERVICE: dict[str, dict] = {}

_routing_pairs = [
    (xsettings.PPA_PHONE_NUMBER_ID,  xsettings.PPA_WEBHOOK_URL,  "PPA"),
    (xsettings.APMC_PHONE_NUMBER_ID, xsettings.APMC_WEBHOOK_URL, "APMC"),
]

for _phone_id, _url, _name in _routing_pairs:
    if _phone_id and _url:
        PHONE_TO_SERVICE[_phone_id] = {"name": _name, "webhook_url": _url}


# ── Background forwarder ──────────────────────────────────────────────────────

async def _forward_to_service(
    service_name: str,
    service_url: str,
    raw_body: bytes,
    headers: dict[str, str],
) -> None:
    """POST the raw webhook body to a downstream service (non-blocking).

    The body is forwarded byte-for-byte (not re-serialized) and the original
    ``X-Hub-Signature-256`` header is propagated, so a downstream service can
    re-validate the Meta signature if it chooses to.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(service_url, content=raw_body, headers=headers)
    except Exception:
        pass


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "services": {
            info["name"]: info["webhook_url"]
            for info in PHONE_TO_SERVICE.values()
        },
    }


@app.get("/")
async def root() -> PlainTextResponse:
    return PlainTextResponse("WhatsApp Webhook Router — see /health for registered services.")


@app.get("/webhook")
async def webhook_verify(request: Request) -> Response:
    mode      = request.query_params.get("hub.mode")
    token     = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        return PlainTextResponse(challenge or "", status_code=200)

    return Response(status_code=403)


@app.post("/webhook")
async def webhook_receiver(request: Request, background_tasks: BackgroundTasks) -> Response:
    raw_body = await request.body()

    try:
        payload = json.loads(raw_body)
    except Exception:
        return Response(status_code=200)

    phone_number_id = get_phone_number_id(payload)
    service = PHONE_TO_SERVICE.get(phone_number_id)

    if service:
        fwd_headers = {
            "Content-Type": "application/json",
            "X-WA-Service": service["name"],
            "X-WA-Phone-Number-Id": phone_number_id,
        }
        signature = request.headers.get("x-hub-signature-256")
        if signature:
            fwd_headers["X-Hub-Signature-256"] = signature

        background_tasks.add_task(
            _forward_to_service,
            service["name"],
            service["webhook_url"],
            raw_body,
            fwd_headers,
        )
    return Response(status_code=200)



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=False)