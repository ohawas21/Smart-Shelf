# 🛒 Smart Shelf — IoT Inventory Management System

A browser-based Smart Shelf simulator that replicates a real retail IoT pipeline. Instead of physical hardware, a drag and drop interface acts as the sensor input — products are dragged onto shelves, weights update in real time, and email alerts fire when stock drops below a configurable threshold. All data flows through a real Azure IoT pipeline.

Built as part of the Applied AI program at **TH Rosenheim**.

**Live Demo:** https://web-production-57f08.up.railway.app

---

## The Idea

Traditional smart shelf systems rely on physical load cells and microcontrollers to measure shelf weight. In this project, we replaced the physical hardware entirely with a virtual simulator — a browser-based drag and drop interface that generates the same weight data and sends it through the exact same Azure IoT pipeline a real device would use.

This means the entire cloud architecture is real and functional — only the data source is virtual.

---

## Architecture

```
Browser UI (drag & drop)
        ↓ HTTP REST + WebSocket
FastAPI Backend
        ↓ HTTP POST (SAS token auth)
Azure IoT Hub
        ↓
Azure Stream Analytics
        ↓
Azure Cosmos DB
        ↓
SendGrid (email alerts)
```

---

## How It Works

1. The user drags a product from the panel onto a shelf in the browser
2. The browser calls `POST /api/shelf/{id}/add` on the FastAPI backend
3. FastAPI updates the shelf weight and broadcasts the change via WebSocket — the UI updates instantly
4. FastAPI generates a SAS token and sends an HTTP POST to Azure IoT Hub with the current weight, threshold, and `low_stock` flag
5. Azure Stream Analytics reads the IoT Hub stream and writes every reading to Cosmos DB
6. When weight drops below the threshold and a product is removed:
   - The shelf card turns red in the UI
   - An alert banner appears in the event log
   - A SendGrid email is sent to the configured address with full shelf details
   - IoT Hub receives a message with `low_stock: true`

---

## Features

- **Drag & drop UI** — drag products from the panel onto any of the 3 shelves
- **Real-time updates** — WebSocket keeps the UI in sync without page refresh
- **Per-shelf thresholds** — adjustable alert threshold via slider (100g–2000g)
- **Low stock detection** — shelf turns red when weight drops below threshold
- **Email alerts** — SendGrid sends a formatted HTML email on every low stock event
- **Azure IoT Hub integration** — every weight change is posted as an IoT device message
- **Event log** — real-time activity log displayed in the UI sidebar

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, Vanilla JavaScript |
| Real-time | WebSocket (FastAPI + uvicorn[standard]) |
| Backend | FastAPI, Python 3 |
| IoT Messaging | Azure IoT Hub (HTTP REST + SAS token) |
| Stream Processing | Azure Stream Analytics |
| Database | Azure Cosmos DB (Serverless) |
| Email | SendGrid |
| Deployment | Railway |

---

## Azure Resources

| Resource | Type |
|---|---|
| `smart-shelf-hub` | Azure IoT Hub |
| `smart-shelf-db` | Azure Cosmos DB |
| `smart-shelf-analytics` | Azure Stream Analytics |

### IoT Devices
Three devices registered in IoT Hub — one per shelf:
- `shelf-a`
- `shelf-b`
- `shelf-c`

Each device has its own connection string used by the backend to authenticate HTTP messages as if they came from a real physical device.

---

## Products

| Product | Weight |
|---|---|
| 🥫 Canned Food | 500g |
| 🧴 Shampoo | 300g |
| 🍫 Chocolate | 200g |
| 🧃 Juice | 250g |
| 💊 Medicine | 100g |

---

## Project Structure

```
Smart-Shelf/
├── main.py               ← FastAPI server, IoT Hub REST client, WebSocket, email alerts
├── templates/
│   └── index.html        ← Browser UI — shelves, drag & drop, event log
├── static/
│   ├── css/style.css     ← Shelf layout, weight bars, alert colours
│   └── js/app.js         ← WebSocket client, drag & drop logic, API calls
├── requirements.txt
├── Procfile              ← Railway deployment start command
└── .env                  ← Credentials (never committed)
```

---

## Environment Variables

```env
SENDGRID_API_KEY=SG.xxxx
ALERT_EMAIL=your@email.com
AZURE_IOT_HUB_CONNECTION_STRING=HostName=...
AZURE_IOT_CONNECTION_STRING_SHELF_A=HostName=...;DeviceId=shelf-a;SharedAccessKey=...
AZURE_IOT_CONNECTION_STRING_SHELF_B=HostName=...;DeviceId=shelf-b;SharedAccessKey=...
AZURE_IOT_CONNECTION_STRING_SHELF_C=HostName=...;DeviceId=shelf-c;SharedAccessKey=...
AZURE_COSMOS_CONNECTION_STRING=AccountEndpoint=...
```

---

## Deployment

The app is deployed on **Railway** at `https://web-production-57f08.up.railway.app`.

Railway connects directly to the `main` branch of this GitHub repo and redeploys automatically on every push.

The start command is defined in `Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

All environment variables are configured in the Railway dashboard — no credentials are stored in the repository.

---

## Running Locally

```bash
git clone https://github.com/ohawas21/Smart-Shelf.git
cd Smart-Shelf
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Create a .env file with your credentials
uvicorn main:app --reload --port 8000
```

Then open `http://127.0.0.1:8000` in your browser.

---

## Team

Dylan Cilett · Jochen Czuck · Jonas Datzmann · Saruni Fernando · Omar Hawas

TH Rosenheim — Applied AI Program