# 🛒 Smart Shelf — IoT Inventory Management System

![image](https://github.com/user-attachments/assets/4b3d3244-ef37-4f2f-abc0-65cc674a48d0)

## Short Description

The Smart Shelf project is an IoT-based inventory management system designed to monitor and manage stock levels in real-time. Utilizing sensors and cloud services, the system alerts users when stock levels are low, ensuring timely restocking and efficient inventory management.

The project supports **two modes**:
- **Hardware mode** — real load cells connected to a Raspberry Pi sending weight data to Azure
- **Simulator mode** — a browser-based drag & drop interface that replicates the exact same IoT pipeline without any physical hardware

---

## Motivation

The motivation behind the Smart Shelf project is to streamline inventory management processes, reduce manual labor, and prevent stockouts. By leveraging IoT technology, businesses can maintain optimal stock levels, enhance operational efficiency, and improve customer satisfaction.

---

## MVP / North Star

The MVP of the Smart Shelf project is a functional system that includes sensor integration, data processing, and real-time notifications for low stock levels. The North Star goal is to develop a comprehensive inventory management solution with advanced analytics and automated restocking capabilities.

---

## Architecture

### Logical Architecture

1. **Sensors / Simulator**: Load cells (hardware) or browser UI (simulator) measure shelf weight
2. **IoT Hub**: Collects weight readings from devices and forwards them to the cloud
3. **Stream Analytics**: Processes incoming data streams in real-time
4. **Cosmos DB**: Stores processed data for historical analysis and reporting
5. **Notification Service**: Sends email alerts via SendGrid when stock drops below threshold

### Technical Architecture

```
[Hardware Mode]
Load Cells → HX711 Amplifier → Raspberry Pi → Azure IoT Hub

[Simulator Mode]
Browser UI (drag & drop) → FastAPI Backend → Azure IoT Hub

                    ↓ (both modes converge here)
            Azure IoT Hub (smart-shelf-hub)
                    ↓
        Azure Stream Analytics (smart-shelf-analytics)
                    ↓
            Azure Cosmos DB (smart-shelf-db)
                    ↓
            SendGrid → Email Alert → Inbox
```

![image](https://github.com/user-attachments/assets/6860032f-a6f2-4fd8-9e8c-1da8eb512dfb)

---

## Hardware Components (Physical Mode)

- Load cells (weight sensors)
- HX711 amplifier
- Raspberry Pi microcontroller

## Software Components

- FastAPI backend (REST API + WebSocket server)
- Azure IoT Hub — device communication
- Azure Stream Analytics — real-time data processing
- Azure Cosmos DB — data storage
- SendGrid — email notification service

---

## Setup Guide

### Option A — Hardware Setup (Raspberry Pi)

#### Hardware Wiring
1. **Connect Load Cells**: Connect load cells to each other to form a full bridge
2. **Connect Amplifier**: Connect the HX711 amplifier to the load cells
3. **Connect Microcontroller**: Connect the HX711 to the Raspberry Pi GPIO pins
4. **Microcontroller Configuration**: Program the Raspberry Pi to read data from load cells

#### Raspberry Pi Software
```bash
sudo apt-get update
sudo apt-get install python3-pip
pip3 install RPi.GPIO hx711 azure-iot-device
git clone https://github.com/ohawas21/smart-shelf
cd smart-shelf
python3 src/calibration.py  # Calibrate the sensors
python3 src/Main.py         # Start data collection
```

---

### Option B — Browser Simulator Setup (No Hardware Required)

As an alternative to physical hardware, this project includes a **full browser-based simulator** that replicates the exact same Azure IoT pipeline. Instead of real load cells and a Raspberry Pi, a FastAPI backend acts as the virtual device — sending the same MQTT messages to Azure IoT Hub as real hardware would.

#### What the Simulator Does

- Provides a drag & drop web interface with three virtual shelves (Shelf A, B, C)
- Each shelf has a configurable weight threshold (100g–2000g, default 500g)
- Dragging a product onto a shelf increases its weight in real time
- Removing a product decreases its weight
- When weight drops below the threshold, the shelf turns red and a low-stock alert fires
- Every weight change is sent to Azure IoT Hub as an MQTT message — identical to real sensor data
- A WebSocket connection keeps the UI updated in real time without page refreshes
- Email alerts are sent via SendGrid when low stock is detected

#### Products Available in the Simulator

| Product | Weight |
|---|---|
| Canned Food | 500g |
| Shampoo | 300g |
| Chocolate | 200g |
| Juice | 250g |
| Medicine | 100g |

#### Local Setup

**Prerequisites**
- Python 3.11+
- Azure account with IoT Hub created
- SendGrid account with a verified sender identity

**1 — Clone the repository**
```bash
git clone https://github.com/ohawas21/smart-shelf
cd smart-shelf
```

**2 — Create and activate a virtual environment**

Mac:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

**3 — Install dependencies**
```bash
pip install -r requirements.txt
pip install 'uvicorn[standard]'
```

> **Important:** `uvicorn[standard]` is required for WebSocket support. Without it the UI will show "Disconnected" even though the server starts normally.

**4 — Configure environment variables**

Create a `.env` file in the project root:
```bash
AZURE_IOT_CONNECTION_STRING_SHELF_A=HostName=...
AZURE_IOT_CONNECTION_STRING_SHELF_B=HostName=...
AZURE_IOT_CONNECTION_STRING_SHELF_C=HostName=...
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxx
ALERT_EMAIL=your@email.com
```

Get the connection strings from Azure Portal → IoT Hub → Devices → select device → Primary Connection String.

**5 — Run the server**
```bash
uvicorn main:app --reload --port 8000
```

**6 — Open the simulator**

Navigate to `http://127.0.0.1:8000` in your browser. You should see **● Connected** in the top bar.

---

### Azure Infrastructure Setup

#### 1 — IoT Hub
- Create an IoT Hub (`smart-shelf-hub`) in Azure
- Register three devices: `shelf-a`, `shelf-b`, `shelf-c`
- Copy each device's Primary Connection String into `.env`

#### 2 — Cosmos DB
- Create a Cosmos DB account (`smart-shelf-db`, Serverless mode)
- In Data Explorer → New Container:
  - Database: `SmartShelf`
  - Container: `ShelfReadings`
  - Partition key: `/shelf_id`

#### 3 — Stream Analytics
- Create a Stream Analytics job (`smart-shelf-analytics`, 1 Streaming Unit)
- Add Input: IoT Hub → alias `shelf-input`, Consumer group `$Default`, JSON / UTF-8
- Add Output: Cosmos DB → alias `shelf-output`, database `SmartShelf`, container `ShelfReadings`, document id `shelf_id`
- Set the query:
```sql
SELECT
    shelf_id,
    shelf_name,
    weight,
    threshold,
    low_stock,
    timestamp,
    System.Timestamp() AS event_time
INTO
    [shelf-output]
FROM
    [shelf-input]
```
- Start the job → **Now**

#### 4 — SendGrid Email Alerts
- Create a free SendGrid account at [sendgrid.com](https://sendgrid.com)
- Create a Sender Identity with your email address and verify it
- Go to Settings → API Keys → Create API Key (Full Access)
- Copy the `SG.` key into `.env` as `SENDGRID_API_KEY`
- Set `ALERT_EMAIL` to the address you want alerts delivered to

---

## How It Works End to End

1. User drags a product onto a shelf in the browser
2. Browser calls `POST /api/shelf/{id}/add` on the FastAPI backend
3. Backend updates shelf weight and broadcasts the change via WebSocket — the UI updates instantly
4. Backend sends an MQTT message to Azure IoT Hub with the current weight and threshold
5. Stream Analytics reads the IoT Hub stream and writes every reading to Cosmos DB
6. When weight drops below the threshold, `low_stock: true` is set in the IoT message
7. The backend fires a SendGrid email alert directly to `ALERT_EMAIL`
8. The shelf card turns red in the UI and an alert banner appears for 5 seconds

---

## Project Structure

```
smart-shelf/
├── main.py                  ← FastAPI server, IoT Hub client, WebSocket, email
├── templates/
│   └── index.html           ← Browser UI (drag & drop, shelves, event log)
├── static/
│   ├── css/style.css        ← Shelf layout, weight bars, colour states
│   └── js/app.js            ← WebSocket client, drag & drop, API calls
├── requirements.txt
└── .env                     ← API keys and connection strings (never commit this)
```

---

## Costs

### Hardware (Physical Mode)
| Item | Cost |
|---|---|
| Load cells + HX711 amplifier | $13.99 |
| Raspberry Pi | $35.00 |
| Breadboard | $2.54 |

### Azure Services
![cost1.png](load-cell/images/cost1.png)
![cost2.png](load-cell/images/cost2.png)

---

## Team

Dylan Cilett · Jochen Czuck · Jonas Datzmann · Saruni Fernando · Omar Hawas

TH Rosenheim — Applied AI Program