# 🌐 NetSuite Pro — Advanced Subnetting & Network Planning Tool

A professional, multi-page Flask web application for subnetting and network planning
with a modern glassmorphism UI, dark mode, binary visualization, and Chart.js graphs.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open in browser
http://localhost:5000
```

## 📁 Project Structure

```
subnet_tool/
├── app.py                  # Flask backend + all API logic
├── requirements.txt
├── templates/
│   ├── base.html           # Sidebar layout, theme toggle
│   ├── index.html          # Dashboard with quick calculator
│   ├── calculator.html     # Full subnet calculator + charts
│   ├── generator.html      # Subnet generator (by count / hosts)
│   ├── vlsm.html           # VLSM / variable-length allocation
│   ├── tools.html          # CIDR converter, IP validator, planner
│   └── simulation.html     # Step-by-step binary simulation
└── static/
    ├── css/style.css       # Glassmorphism + gradient design system
    └── js/main.js          # Shared utilities, theme, API helpers
```

## ✨ Features

| Feature | Details |
|---|---|
| **Subnet Calculator** | Network ID, broadcast, first/last host, masks, IP class, binary |
| **Subnet Generator** | Split by # of subnets OR hosts per subnet |
| **VLSM Calculator** | Department-based optimal allocation with efficiency % |
| **Step Simulation** | 6-step binary walkthrough with highlighted network/host bits |
| **CIDR ↔ Mask Converter** | Instant two-way conversion + reference table |
| **IP Validator** | Class, type (private/public/loopback/multicast), binary |
| **Smart Planner** | Suggest optimal CIDR based on host & subnet requirements |
| **Charts** | Doughnut, bar, pie charts via Chart.js |
| **Dark Mode** | Gradient light ↔ dark toggle, saved in localStorage |
| **Export** | CSV and TXT download for all result tables |

## 🎨 UI Design

- **Glassmorphism** cards with `backdrop-filter: blur`
- **Gradient** color palette: Blue→Purple, Pink→Red, Cyan→Blue
- **Poppins** font for UI + **JetBrains Mono** for binary/IP values
- **Animated** background blobs, hover effects, card entrance animations
- **Responsive** sidebar layout (mobile hamburger)
- **Dark mode** with gradient themes preserved

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/calculate` | Full subnet info |
| POST | `/api/generate` | Generate subnets |
| POST | `/api/vlsm` | VLSM allocation |
| POST | `/api/simulation` | Step simulation data |
| POST | `/api/planner` | Smart recommendations |
| POST | `/api/tools/cidr_to_mask` | CIDR → mask |
| POST | `/api/tools/mask_to_cidr` | Mask → CIDR |
| POST | `/api/tools/validate_ip` | IP validation |
| POST | `/api/export` | CSV/TXT download |
