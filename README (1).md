<div align="center">

<img src="dashboard/logo.png" alt="FIRO Logo" width="110" />

# 🔥 FIRO — Wildfire Detection System
### Edge AI · Real-Time Monitoring · Forest Fire Early Warning

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![TensorFlow Lite](https://img.shields.io/badge/TFLite-INT8-FF6F00?style=flat-square&logo=tensorflow&logoColor=white)](https://tensorflow.org/lite)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28?style=flat-square&logo=firebase&logoColor=black)](https://firebase.google.com)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-5-C51A4A?style=flat-square&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

> **FIRO** is a lightweight, real-time wildfire detection system built for resource-constrained edge devices. A MobileNetV2 model — optimized to TensorFlow Lite INT8 — runs directly on a Raspberry Pi 5, classifying forest camera images and pushing fire alerts to a web dashboard and WhatsApp, all without relying on cloud compute.

**BS Final Year Project · Department of Data Science · University of Kotli, AJK**  
*Ahmed Ali · Seher Ishtiaq · Supervisor: Mr. Nabeel Ali · Session 2021–2025*

---

</div>

## 📋 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Repository Structure](#-repository-structure)
- [Model Performance](#-model-performance)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Dashboard Setup](#1-dashboard-setup)
  - [Raspberry Pi Setup](#2-raspberry-pi-setup)
  - [Firebase Configuration](#3-firebase-configuration)
- [Dashboard Pages](#-dashboard-pages)
- [Edge Device Pipeline](#-edge-device-pipeline)
- [Results](#-results)
- [Motivation](#-motivation)
- [Future Work](#-future-work)
- [Authors](#-authors)

---

## 🌐 Overview

Wildfires in Pakistan — especially in Azad Jammu & Kashmir — are increasingly devastating. In 2024 alone, **2,214 high-confidence VIIRS fire alerts** were recorded across Pakistan. Traditional detection relies on satellite imagery (with 16-day revisit cycles), manual watchtowers, and public reporting — all too slow for early intervention.

**FIRO** (Fire Intelligence & Response Observatory) solves this by putting AI directly on the ground:

- A **USB camera** mounted on a forest tower feeds images to a **Raspberry Pi 5**
- An **INT8-quantized MobileNetV2** model runs fully on-device — no cloud compute needed
- Only lightweight metadata (fire/no-fire label, confidence, GPS, timestamp) is sent to **Firebase**
- Alerts reach **Forest Department staff via WhatsApp** and a **real-time web dashboard**

**97.5% accuracy · <1s inference latency · Runs on a $80 edge device**

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EDGE LAYER                                   │
│                                                                     │
│   📷 USB Camera                                                     │
│       │  RGB frames                                                 │
│       ▼                                                             │
│   🖥️  Raspberry Pi 5                                                │
│   ┌─────────────────────────────────────────────────┐              │
│   │  1. Capture image at timed intervals             │              │
│   │  2. Resize to 224×224 · Normalize pixels        │              │
│   │  3. Run MobileNetV2 Lite (INT8 TFLite)          │              │
│   │  4. Get: { label, confidence, timestamp, GPS }  │              │
│   └─────────────────────────────────────────────────┘              │
└──────────────────────────┬──────────────────────────────────────────┘
                           │  Metadata only (no raw images)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CLOUD LAYER (Firebase)                        │
│                                                                     │
│   🔥 Firestore → stores fire_logs collection                        │
│   🔐 Firebase Auth → secures dashboard access                       │
│   📡 Triggers → WhatsApp alerts on fire detection                   │
└───────────────┬─────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DASHBOARD LAYER                                 │
│                                                                     │
│   🌐 Web Dashboard (HTML/JS + Python Dash)                          │
│   ├── Live map with camera locations (Leaflet)                      │
│   ├── Real-time alert panel (auto-polls every 5 s)                  │
│   ├── Event log history (filterable)                                │
│   └── Dark mode · PWA-enabled                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🧠 **On-Device Inference** | MobileNetV2 Lite (INT8) runs entirely on Raspberry Pi — no cloud compute |
| ⚡ **Real-Time Detection** | Images captured and classified continuously; results pushed in seconds |
| 📡 **Minimal Bandwidth** | Only compact metadata sent to Firebase — no raw image uploads |
| 🗺️ **Live Map Dashboard** | Leaflet-powered interactive map shows all camera locations and fire status |
| 🚨 **Instant Alerts** | WhatsApp notifications delivered to forest staff on fire detection |
| 🔐 **Secure Login** | Firebase Authentication guards dashboard access |
| 📜 **Event Log History** | Full searchable log of all detection events with timestamps |
| 🌙 **Dark / Light Mode** | Full theme support across all dashboard pages |
| 📱 **PWA Ready** | Installable as a mobile app via service worker + manifest |
| 📊 **Python Dash View** | Alternative Plotly/Dash analytics panel (`app.py`) for deeper analysis |

---

## 🛠 Tech Stack

### Edge Device (Raspberry Pi 5)
| Component | Technology |
|---|---|
| Language | Python 3.11 |
| ML Framework | TensorFlow Lite (INT8) |
| Model | MobileNetV2 (fine-tuned, quantized) |
| Camera | USB Camera (OpenCV capture) |
| Cloud Push | Firebase Admin SDK |

### Dashboard (Web)
| Component | Technology |
|---|---|
| Frontend | HTML5, Tailwind CSS, Vanilla JS |
| Maps | Leaflet.js |
| Auth | Firebase Authentication |
| Database | Cloud Firestore |
| Icons | Font Awesome 6 |
| PWA | Service Worker + Web App Manifest |
| Analytics Panel | Python Dash + Plotly |

### Cloud & Infrastructure
| Component | Technology |
|---|---|
| Database | Firebase Firestore |
| Authentication | Firebase Auth (Email/Password) |
| Alerts | WhatsApp (via Firebase trigger) |
| Hosting | Firebase Hosting (recommended) |

---

## 📁 Repository Structure

```
FIRO-FYP/
│
├── 📂 dashboard/                    # Web dashboard frontend + Dash backend
│   ├── index.html                   # Main monitoring dashboard (live map, alerts)
│   ├── login.html                   # Firebase Auth login/signup page
│   ├── logs.html                    # Historical fire event log page
│   ├── settings.html                # User preferences (theme toggle)
│   ├── login.css                    # Login page styles
│   ├── login.js                     # Legacy login helper (superseded by login.html)
│   ├── script.js                    # Firebase initialization script
│   ├── service-worker.js            # PWA offline caching
│   ├── manifest.json                # PWA web app manifest
│   ├── logo.png                     # FIRO / university logo
│   ├── app.py                       # Python Dash analytics dashboard
│   └── service_account_key.json     # ⚠️  SECRET — never commit (in .gitignore)
│
├── 📂 Models Source Files/          # Trained & optimized ML model
│   └── mobilenetv2_fire_detection.tflite   # INT8 quantized TFLite model
│
├── 📂 raspberry-pi/                 # Edge device inference code
│   ├── capture.py                   # Camera capture + inference loop
│   ├── firebase_push.py             # Push results to Firestore
│   └── requirements.txt             # Pi dependencies
│
├── .gitignore                       # Ignores secrets, venvs, IDE files
└── README.md                        # You are here
```

> **Note:** The `raspberry-pi/` folder contains the on-device code that runs the inference loop on Raspberry Pi 5. Both codebases share the same Firebase project.

---

## 📊 Model Performance

### Model Comparison (Same Wildfire Dataset)

| Model | Parameters | Test Accuracy |
|---|---|---|
| **MobileNetV2 (Proposed)** | **2.6 M** | **97.50%** ✅ |
| VGG-16 | 15.24 M | 93.23% |
| ResNet-50 | ~25 M | 96.59% |
| EfficientNet-B0 | 4.38 M | 98.47% |
| EfficientNetV2-B0 | 6.25 M | 97.58% |
| YOLOv11 Nano | 1.53 M | 96.40% |

> MobileNetV2 was chosen despite not being the highest-accuracy model — its 2.6M parameter count, TFLite compatibility, and INT8 quantization make it the only realistic choice for real-time inference on Raspberry Pi 5.

### Quantized Model (Deployed)

| Metric | MobileNetV2 (FP32) | MobileNetV2 Lite (INT8) |
|---|---|---|
| Accuracy | 0.96 | 0.95 |
| Precision | 0.96 | 0.95 |
| Recall | 0.96 | 0.95 |
| F1-Score | 0.96 | 0.95 |

### Dataset
- **Total images:** 6,247 (Fire: 2,821 · No Fire: 3,427)
- **Train / Val / Test:** 4,350 / 656 / 1,241
- **Image size:** 224 × 224 RGB
- **Source:** Kaggle forest fire dataset

### Real-World Night Test
12 images captured in actual forest fires near **Khuiratta and Nakyal, AJK (Dec 2025 – Jan 2026)** → **100% detection accuracy** under low-light, real-world conditions.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or 3.11
- A Firebase project ([create one free](https://console.firebase.google.com))
- Raspberry Pi 5 with Raspberry Pi OS (64-bit)
- USB camera
- Git

---

### 1. Dashboard Setup

**Clone the repo:**
```bash
git clone https://github.com/datixai/FIRO-FYP.git
cd FIRO-FYP
```

**Install Python dependencies (for `app.py` Dash dashboard):**
```bash
cd dashboard
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install dash plotly pandas google-cloud-firestore
```

**Set your Firebase credentials:**
```bash
export GCP_KEY_PATH=/path/to/your/service_account_key.json
```

**Run the Dash analytics dashboard:**
```bash
python app.py
# Open http://127.0.0.1:8050
```

**For the HTML dashboard** (`index.html`, `login.html`, etc.) — simply open in a browser or deploy to Firebase Hosting:
```bash
npm install -g firebase-tools
firebase login
firebase init hosting
firebase deploy
```

---

### 2. Raspberry Pi Setup

```bash
# On Raspberry Pi 5 (SSH in or open terminal)
git clone https://github.com/datixai/FIRO-FYP.git
cd FIRO-FYP/raspberry-pi

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Place your Firebase service account key** (from Firebase Console → Project Settings → Service Accounts):
```bash
# Copy the JSON key to the raspberry-pi directory (this file is gitignored)
cp /path/to/service_account_key.json ./service_account_key.json
```

**Run the detection loop:**
```bash
python capture.py
```

The script will:
1. Capture an image via the USB camera every N seconds
2. Resize and normalize to 224×224
3. Run inference using `mobilenetv2_fire_detection.tflite`
4. Push results to Firebase Firestore
5. Trigger WhatsApp alert if fire is detected

---

### 3. Firebase Configuration

1. Go to [Firebase Console](https://console.firebase.google.com) → your project
2. Enable **Firestore Database** — start in production mode
3. Enable **Authentication** → Email/Password provider
4. Create your Firestore collection: `fire_logs`
5. Download **Service Account Key** (Project Settings → Service Accounts → Generate New Private Key)
6. **⚠️ Never commit this file** — it is listed in `.gitignore`

**Firestore document structure** (written by Raspberry Pi):
```json
{
  "timestamp_ms": 1704067200000,
  "timestamp_str": "2026-01-01 12:00:00",
  "detection_class": "Fire",
  "fire_probability": 0.94,
  "camera_location": "Khuiratta Tower 1",
  "coords_x": 33.6844,
  "coords_y": 73.0479,
  "device_id": "rpi5-unit-01"
}
```

---

## 🖥️ Dashboard Pages

### Login Screen
Firebase-authenticated login/signup. Session expires on browser close (session persistence).  
**File:** `dashboard/login.html`

### Main Dashboard (`index.html`)
- **Live Leaflet map** — colour-coded markers (🔴 Fire / 🟢 Safe) at each camera location
- **Alert panel** — pulses red with critical fire alert details when fire is detected
- **Stats cards** — total alerts, active cameras, latest detection time
- **Real-time updates** — auto-polls Firebase every 5 seconds
- **Dark / Light mode** toggle

### Fire Event Log (`logs.html`)
- Full history of all detection events from Firebase
- Filter by: Fire / No Fire / All
- Each entry shows: timestamp, location, confidence score, classification
- Dark mode supported

### Settings (`settings.html`)
- Theme preference (Light / Dark)
- More options in development (alert thresholds, notification recipients)

### Python Dash Dashboard (`app.py`)
- Alternative analytics view using Plotly/Dash
- Scatter mapbox with fire probability bubble sizing
- Recent log table with conditional red highlighting for fire events
- Last-hour data window with 5-second polling

---

## ⚙️ Edge Device Pipeline

```
USB Camera
    │
    │ RGB frame
    ▼
┌─────────────────────────────────────┐
│         Preprocessing               │
│  • Resize → 224 × 224              │
│  • Normalize pixel values [0, 1]   │
│  • Format as float32 tensor        │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   TFLite Interpreter                │
│   mobilenetv2_fire_detection.tflite │
│   (INT8 quantized, ~2.6M params)   │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│         Postprocessing              │
│  • Softmax probabilities           │
│  • Threshold: 0.70 → Fire          │
│  • Add GPS, device ID, timestamp   │
└────────────────┬────────────────────┘
                 │
          ┌──────┴──────┐
          │             │
          ▼             ▼
   Firebase          WhatsApp
   Firestore         Alert
   (metadata)        (if fire)
```

**Training Setup:**
- Framework: TensorFlow 2.x + Keras
- Hardware: NVIDIA Tesla P100 GPU
- Transfer learning: ImageNet pre-trained weights → fine-tuned on wildfire dataset
- Quantization: Post-training INT8 via TFLite Converter + calibration dataset

---

## 📈 Results

- ✅ **97.5% test accuracy** (MobileNetV2 FP32)
- ✅ **95% accuracy** after INT8 quantization (negligible drop)
- ✅ **100% accuracy** on 12 real night-time wildfire images from AJK
- ✅ Sub-second inference on Raspberry Pi 5
- ✅ All 6 unit test cases passed (capture → preprocess → infer → push → alert → display)

---

## 🌍 Motivation

Pakistan recorded **966 high-confidence fire alerts in 2025** and **1,905 in 2024** — the highest ever recorded. The December 2025 Neelum Valley fire and recurring fires in Sherani, Margalla Hills, and Gilgit-Baltistan illustrate the urgent need for early warning systems. Satellite-based tools have 16-day revisit cycles. Manual watchtowers don't scale.

FIRO is designed for exactly this gap: **affordable, deployable, and accurate** — built for the forest conditions of Northern Pakistan and Azad Kashmir.

---

## 🔮 Future Work

- [ ] Multi-sensor fusion (temperature, humidity, gas sensors)
- [ ] Drone-based aerial image integration
- [ ] SMS / mobile push notifications in addition to WhatsApp
- [ ] Temporal modeling for smoke trajectory prediction
- [ ] Federated learning across multiple edge nodes
- [ ] Large-scale long-term field deployment and validation
- [ ] Admin panel for managing camera nodes and alert thresholds

---

## 👥 Authors

| Name | Role | Contact |
|---|---|---|
| **Ahmed Ali** | Group Leader | rajaahmedalikhan97@gmail.com |
| **Seher Ishtiaq** | Member | hania93malik@gmail.com |

**Supervisor:** Mr. Nabeel Ali  
**Institution:** Department of Data Science, Faculty of Computing & Engineering  
University of Kotli, Azad Jammu & Kashmir

---

## 📄 License

This project is released under the [MIT License](LICENSE).  
Built with ❤️ for the forests of Azad Kashmir.

---

<div align="center">
<sub>FIRO · University of Kotli AJK · BS Data Science · 2021–2025</sub>
</div>
