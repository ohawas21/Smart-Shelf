import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from azure.iot.device.aio import IoTHubDeviceClient

load_dotenv()

app = FastAPI(title="Smart Shelf Simulator")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── PRODUCTS ──────────────────────────────────────────────────────────────────
PRODUCTS = {
    "canned_food":  {"name": "Canned Food",  "emoji": "🥫", "weight": 500},
    "shampoo":      {"name": "Shampoo",      "emoji": "🧴", "weight": 300},
    "chocolate":    {"name": "Chocolate",    "emoji": "🍫", "weight": 200},
    "juice":        {"name": "Juice",        "emoji": "🧃", "weight": 250},
    "medicine":     {"name": "Medicine",     "emoji": "💊", "weight": 100},
}

# ── SHELF STATE ───────────────────────────────────────────────────────────────
shelves: Dict = {
    "shelf_a": {"id": "shelf_a", "name": "Shelf A", "products": [], "current_weight": 0, "threshold": 500, "alert_sent": False},
    "shelf_b": {"id": "shelf_b", "name": "Shelf B", "products": [], "current_weight": 0, "threshold": 500, "alert_sent": False},
    "shelf_c": {"id": "shelf_c", "name": "Shelf C", "products": [], "current_weight": 0, "threshold": 500, "alert_sent": False},
}

# ── IOT HUB CLIENTS ───────────────────────────────────────────────────────────
iot_clients: Dict = {}

async def init_iot_clients():
    """Connect each shelf as an IoT device to Azure IoT Hub."""
    mapping = {
        "shelf_a": os.environ.get("AZURE_IOT_CONNECTION_STRING_SHELF_A"),
        "shelf_b": os.environ.get("AZURE_IOT_CONNECTION_STRING_SHELF_B"),
        "shelf_c": os.environ.get("AZURE_IOT_CONNECTION_STRING_SHELF_C"),
    }
    for shelf_id, conn_str in mapping.items():
        if conn_str:
            try:
                client = IoTHubDeviceClient.create_from_connection_string(conn_str, websockets=True)
                await client.connect()
                iot_clients[shelf_id] = client
                print(f"  ✓ {shelf_id} connected to IoT Hub")
            except Exception as e:
                print(f"  ✗ {shelf_id} IoT Hub error: {e}")
        else:
            print(f"  ⚠ {shelf_id} — no connection string in .env")


async def send_iot_message(shelf_id: str, weight: int, threshold: int, alert: bool):
    """Send weight reading to Azure IoT Hub."""
    client = iot_clients.get(shelf_id)
    if not client:
        return

    payload = json.dumps({
        "shelf_id":   shelf_id,
        "shelf_name": shelves[shelf_id]["name"],
        "weight":     weight,
        "threshold":  threshold,
        "low_stock":  alert,
        "timestamp":  datetime.utcnow().isoformat(),
    })

    try:
        from azure.iot.device import Message
        await client.send_message(Message(payload))
        print(f"IoT Hub ← {shelf_id}: {weight}g (alert={alert})")
    except Exception as e:
        print(f"IoT send error: {e}")


# ── WEBSOCKET MANAGER ─────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        disconnected = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.active.remove(ws)

manager = ConnectionManager()


# ── EMAIL ALERT ───────────────────────────────────────────────────────────────
def send_alert_email(shelf_name: str, weight: int, threshold: int, products: list):
    api_key     = os.environ.get("SENDGRID_API_KEY")
    alert_email = os.environ.get("ALERT_EMAIL")

    if not api_key or not alert_email or not api_key.startswith("SG."):
        print("SendGrid not configured — skipping email")
        return False

    product_list = ", ".join([p["name"] for p in products]) or "Empty shelf"

    message = Mail(
        from_email=alert_email,
        to_emails=alert_email,
        subject=f"⚠️ Smart Shelf Alert — {shelf_name} Low Stock",
        html_content=f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
            <h2 style="color:#e74c3c">⚠️ Low Stock Alert</h2>
            <p><strong>{shelf_name}</strong> has dropped below the threshold.</p>
            <table style="width:100%;border-collapse:collapse;margin-top:16px">
                <tr style="background:#f8f9fa">
                    <td style="padding:10px;border:1px solid #dee2e6"><strong>Shelf</strong></td>
                    <td style="padding:10px;border:1px solid #dee2e6">{shelf_name}</td>
                </tr>
                <tr>
                    <td style="padding:10px;border:1px solid #dee2e6"><strong>Current weight</strong></td>
                    <td style="padding:10px;border:1px solid #dee2e6">{weight}g</td>
                </tr>
                <tr style="background:#f8f9fa">
                    <td style="padding:10px;border:1px solid #dee2e6"><strong>Threshold</strong></td>
                    <td style="padding:10px;border:1px solid #dee2e6">{threshold}g</td>
                </tr>
                <tr>
                    <td style="padding:10px;border:1px solid #dee2e6"><strong>Products remaining</strong></td>
                    <td style="padding:10px;border:1px solid #dee2e6">{product_list}</td>
                </tr>
                <tr style="background:#f8f9fa">
                    <td style="padding:10px;border:1px solid #dee2e6"><strong>Time</strong></td>
                    <td style="padding:10px;border:1px solid #dee2e6">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
            </table>
            <p style="margin-top:20px;color:#666">Please restock <strong>{shelf_name}</strong> immediately.</p>
            <p style="color:#999;font-size:12px">Smart Shelf Simulator — IoT Inventory Management</p>
        </div>
        """
    )
    try:
        sg = SendGridAPIClient(api_key)
        sg.send(message)
        print(f"Email sent for {shelf_name}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


# ── STARTUP / SHUTDOWN ────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    print("Connecting to Azure IoT Hub...")
    await init_iot_clients()
    print("Smart Shelf server ready.\n")


@app.on_event("shutdown")
async def shutdown():
    for client in iot_clients.values():
        await client.disconnect()


# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "products": PRODUCTS,
            "shelves":  shelves,
        }
    )


@app.get("/api/state")
async def get_state():
    return {"shelves": shelves, "products": PRODUCTS}


@app.post("/api/shelf/{shelf_id}/add")
async def add_product(shelf_id: str, body: dict):
    product_id = body.get("product_id")
    if shelf_id not in shelves:
        return JSONResponse({"error": "Shelf not found"}, status_code=404)
    if product_id not in PRODUCTS:
        return JSONResponse({"error": "Product not found"}, status_code=404)

    product  = PRODUCTS[product_id]
    shelf    = shelves[shelf_id]
    instance = {
        "id":         f"{product_id}_{datetime.now().timestamp()}",
        "product_id": product_id,
        "name":       product["name"],
        "emoji":      product["emoji"],
        "weight":     product["weight"],
    }
    shelf["products"].append(instance)
    shelf["current_weight"] += product["weight"]
    if shelf["current_weight"] >= shelf["threshold"]:
        shelf["alert_sent"] = False

    asyncio.create_task(send_iot_message(
        shelf_id, shelf["current_weight"], shelf["threshold"], False
    ))

    event = {
        "type":           "weight_update",
        "shelf_id":       shelf_id,
        "shelf_name":     shelf["name"],
        "action":         "add",
        "product":        product["name"],
        "current_weight": shelf["current_weight"],
        "threshold":      shelf["threshold"],
        "alert":          False,
        "timestamp":      datetime.now().isoformat(),
    }
    await manager.broadcast(event)
    return {"shelf": shelf, "event": event}


@app.delete("/api/shelf/{shelf_id}/remove/{instance_id}")
async def remove_product(shelf_id: str, instance_id: str):
    if shelf_id not in shelves:
        return JSONResponse({"error": "Shelf not found"}, status_code=404)

    shelf   = shelves[shelf_id]
    product = next((p for p in shelf["products"] if p["id"] == instance_id), None)
    if not product:
        return JSONResponse({"error": "Product not found"}, status_code=404)

    shelf["products"].remove(product)
    shelf["current_weight"] = max(0, shelf["current_weight"] - product["weight"])

    alert = False
    if shelf["current_weight"] < shelf["threshold"] and not shelf["alert_sent"]:
        shelf["alert_sent"] = True
        alert = True
        asyncio.create_task(asyncio.to_thread(
            send_alert_email,
            shelf["name"],
            shelf["current_weight"],
            shelf["threshold"],
            shelf["products"],
        ))

    asyncio.create_task(send_iot_message(
        shelf_id, shelf["current_weight"], shelf["threshold"], alert
    ))

    event = {
        "type":           "weight_update",
        "shelf_id":       shelf_id,
        "shelf_name":     shelf["name"],
        "action":         "remove",
        "product":        product["name"],
        "current_weight": shelf["current_weight"],
        "threshold":      shelf["threshold"],
        "alert":          alert,
        "timestamp":      datetime.now().isoformat(),
    }
    await manager.broadcast(event)
    return {"shelf": shelf, "event": event}


@app.put("/api/shelf/{shelf_id}/threshold")
async def update_threshold(shelf_id: str, body: dict):
    if shelf_id not in shelves:
        return JSONResponse({"error": "Shelf not found"}, status_code=404)
    shelves[shelf_id]["threshold"]  = body.get("threshold", 500)
    shelves[shelf_id]["alert_sent"] = False
    await manager.broadcast({
        "type":      "threshold_update",
        "shelf_id":  shelf_id,
        "threshold": shelves[shelf_id]["threshold"],
        "timestamp": datetime.now().isoformat(),
    })
    return {"shelf": shelves[shelf_id]}


# ── WEBSOCKET ─────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial state so the UI renders immediately on connect
        await websocket.send_json({
            "type":     "init",
            "shelves":  shelves,
            "products": PRODUCTS,
        })
        # Keep connection alive with a heartbeat every 30 seconds
        # (browser never sends text, so receive_text() would block/crash)
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except (WebSocketDisconnect, Exception):
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)