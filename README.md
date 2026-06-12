# WhatsApp Webhook Router

Receives Meta webhook events and forwards them to downstream services based on the receiving `phone_number_id`.

| Phone number ID env var | Forwarded to |
|---|---|
| `PPA_PHONE_NUMBER_ID` | `PPA_WEBHOOK_URL` |
| `APMC_PHONE_NUMBER_ID` | `APMC_WEBHOOK_URL` |
| `THS_PHONE_NUMBER_ID` | `THS_WEBHOOK_URL` |

## Setup

1. Copy `.env.example` to `.env` and fill in the values:

```env
WEBHOOK_VERIFY_TOKEN=

PPA_PHONE_NUMBER_ID=
PPA_WEBHOOK_URL=

APMC_PHONE_NUMBER_ID=
APMC_WEBHOOK_URL=

THS_PHONE_NUMBER_ID=
THS_WEBHOOK_URL=
```

2. Install dependencies:

```bash
uv add -r requirements.txt
```

3. Run the server:

```bash
uvicorn main:app --port 8000 --reload
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check message |
| `GET` | `/health` | Lists registered services and their webhook URLs |
| `GET` | `/webhook` | Meta webhook verification handshake |
| `POST` | `/webhook` | Receives and forwards webhook events |