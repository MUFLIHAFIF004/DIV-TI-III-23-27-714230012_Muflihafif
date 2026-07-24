# 🧪 Agentic Integration Testing System

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini%20AI-2.5--Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas%20Cloud-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Vercel](https://img.shields.io/badge/Deployment-Vercel%20Serverless-000000?style=for-the-badge&logo=vercel&logoColor=white)

**Agentic Integration Testing System** adalah platform pengujian integrasi API Microservices otomatis berbasis **Micro-Agentic Architecture**. Sistem ini menggunakan gabungan **2 Agen Deterministik (Non-LLM)** untuk pembentukan & eksekusi *test suite* yang super cepat (0 ms) serta **1 LLM Utama (Google Gemini AI)** sebagai *Master Evaluator* untuk menyintesis skor kesehatan integrasi (*Health Score %*), analisis akar masalah (*Root Cause*), dan laporan analisis teknis berformat **Markdown (MD)**.

Sistem ini dilengkapi antarmuka **Conversational AI QA Chat Studio**, dukungan pengunduhan file mentah **JSON**, serta mekanisme pencatatan riwayat otomatis ke **MongoDB Atlas Cloud** dan folder lokal (`app/output/`).

---

## 🔄 Workflow Sistem & Arsitektur Sekuensial

Berikut adalah diagram alur kerja (*Workflow Diagram*) dari awal hingga akhir yang menggambarkan bagaimana ketiga Micro-Agent saling berkomunikasi dengan layer antarmuka, server, dan penyimpanan:

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 User / QA Tester
    participant GUI as 💬 Conversational Chat UI (public/)
    participant FastAPI as 🚀 FastAPI Server (app/main.py)
    participant Agent1 as ⚡ Agent 1: Test Generator
    participant Agent2 as 🏃 Agent 2: Async Executor
    participant TargetAPI as 🌐 Target Microservice API
    participant Agent3 as 🧠 Agent 3: Gemini LLM Evaluator
    participant DB as ☁️ MongoDB Atlas / In-Memory
    participant Disk as 📁 Local Disk (app/output/)

    User->>GUI: 1. Masukkan Target URL & Deskripsi Skenario
    GUI->>FastAPI: 2. Request POST /api/v1/test-integration
    
    rect rgb(239, 246, 255)
        note right of FastAPI: 🤖 Micro-Agentic Processing Pipeline
        FastAPI->>Agent1: 3. Trigger Skenario Pembentukan Test Cases
        Agent1-->>FastAPI: 4. Hasil 3 Test Payloads (Positif, Edge, Negatif)
        
        FastAPI->>Agent2: 5. Eksekusi Test Suite secara Async
        loop Untuk Setiap Test Case (3 Skenario)
            Agent2->>TargetAPI: 6. HTTP POST Request (Payload Uji)
            TargetAPI-->>Agent2: 7. Return HTTP Status Code, Latensi (ms), & Body
        end
        Agent2-->>FastAPI: 8. Kompilasi Log Latensi & Status Code
        
        FastAPI->>Agent3: 9. Sintesis Log Eksekusi & Evaluasi Integrasi
        Agent3-->>FastAPI: 10. Output Health Score %, Root Cause, & Report MD
    end

    rect rgb(240, 253, 244)
        note right of FastAPI: 💾 Persistence & Output Export Layer
        FastAPI->>DB: 11. Save Document History ke MongoDB Atlas
        FastAPI->>Disk: 12. Auto Save File JSON (raw_json/) & MD (reports/)
    end

    FastAPI-->>GUI: 13. Return Response JSON Lengkap
    GUI->>User: 14. Render Visual Markdown (Marked.js), Chat Bubble, & Tombol Download
```

---

## 🎯 Tahapan Workflow Rinci (Step-by-Step Workflow)

1. **Tahap 1: Inisiasi Pengujian (Input User)**:
   - Pengguna memasukkan **URL Endpoint Target** dan **Deskripsi Skenario Uji** pada antarmuka *Conversational QA Chat Studio*.
2. **Tahap 2: Pembentukan Test Suite (Agent 1 - Generator)**:
   - **Agent 1** (Deterministik) membangkitkan 3 variasi *payload* otomatis tanpa membuang token LLM:
     - *Positif Case*: Data valid sesuai struktur normal.
     - *Edge Case*: Data batas (boundary/buffer maksimum).
     - *Negatif Case*: Data rusak/invalid.
3. **Tahap 3: Eksekusi HTTP Async (Agent 2 - Executor)**:
   - **Agent 2** (Async HTTP Runner via `httpx`) mengirimkan panggilan POST ke target API, mencatat HTTP Status Code, dan mengukur durasi latensi dalam milidetik (`latency_ms`).
4. **Tahap 4: Sintesis Evaluasi AI (Agent 3 - Gemini LLM Evaluator)**:
   - **Agent 3** mengonsolidasi seluruh log Agen 1 & 2. Gemini AI dipanggil untuk menghitung *Integration Health Score %*, analisis akar masalah, serta laporan teknis berformat Markdown (`report_md`).
5. **Tahap 5: Penyimpanan & Output**:
   - Hasil pengujian disimpan ke **MongoDB Atlas Cloud** dan berkas fisik lokal (`app/output/raw_json/` & `app/output/reports/`).
   - GUI merender laporan Markdown secara estetik menggunakan **Marked.js** dan menyediakan tombol `📥 Download Output JSON`.

---

## 💡 Logika Kriteria Hasil Test Cases: LULUS (PASS) vs GAGAL (FAIL)

Setiap pengujian menghasilkan log status dari Agent 1 & Agent 2. Berikut adalah penjelasan mendetail mengenai logika penentuan **LULUS** atau **GAGAL** berdasarkan respon HTTP Status Code dari target API:

| Tipe Test Case | Contoh Response Status Code | Hasil | Penjelasan Logika Sistem |
| :--- | :---: | :---: | :--- |
| **Positif (Valid Payload)** | `405 Method Not Allowed` / `500 Error` | ❌ **GAGAL** | **Ekspektasi**: HTTP `200 OK` / `201 Created`. Karena API mengembalikan error 405 (Method Not Allowed) / 500, berarti endpoint valid tidak dapat diproses dengan benar. |
| **Edge Case (Boundary Input)** | `503 Service Unavailable` / `500 Server Error` | ❌ **GAGAL** | **Ekspektasi**: HTTP `200` s/d `499`. Jika API mengalami error server 5xx saat diberi input batas maksimum, berarti sistem tidak tahan terhadap *edge case* (vulnerable/crash). |
| **Negatif (Invalid Payload)** | `405 Method Not Allowed` / `400 Bad Request` | ✅ **LULUS** | **Ekspektasi**: API **HARUS MENOLAK** request invalid (Kelompok HTTP `4xx` Client Error). Karena API mengembalikan 405 (yang merupakan kelompok 4xx), API dinilai **sukses menolak** data invalid secara aman. |

### 📌 Contoh Kasus Eksekusi Real:

```text
Test Case                   Status    Latensi     Hasil
Positif (Valid Payload)     405       624.17 ms   GAGAL   -> (Karena 405 != 200/201 Sukses)
Edge Case (Boundary Input)  503       564.95 ms   GAGAL   -> (Karena 503 adalah Server Crash 5xx)
Negatif (Invalid Payload)   405       569.04 ms   LULUS   -> (Karena 405 adalah Client Error 4xx, sesuai ekspektasi penolakan data invalid)
```

---

## 🛠️ Teknologi & Dependensi (Tech Stack)

### Backend Framework & Libraries
* **Python 3.10+**: Bahasa pemrograman utama.
* **FastAPI **: Framework backend async modern berkinerja tinggi.
* **google-genai **: SDK resmi Google GenAI untuk integrasi Gemini AI (`gemini-2.5-flash`).
* **httpx **: Client HTTP async untuk eksekusi panggilan API otomatis.
* **motor ** & **pymongo (>=4.0.0)**: Driver MongoDB async untuk penyimpanan cloud.
* **pydantic **: Validasi dan kontrat data schema.
* **uvicorn **: Server ASGI lokal.

### Frontend Technologies
* **HTML5 & Vanilla JavaScript (ES6+)**: Logika interaktif obrolan chat & Blob downloader.
* **Tailwind CSS (CDN)**: Framework CSS untuk styling *Royal & Ice Blue*.
* **Marked.js (CDN)**: Markdown parser untuk merender laporan teknis di browser.
* **FontAwesome 6 (CDN)**: Ikon visual antarmuka.

---

## ⚙️ Panduan Instalasi & Penggunaan Lokal

### 1. Prasyarat Sistem
* Python version 3.10 atau lebih baru.
* Git & Package Manager (`pip`).

### 2. Clone Repositori & Persiapan Environment
```bash
# Clone repositori ke komputer Anda
git clone https://github.com/username/agentic-integration-testing.git

# Masuk ke direktori proyek
cd agentic-integration-testing

# Buat virtual environment (opsional tetapi direkomendasikan)
python -m venv venv

# Aktivasi virtual environment (Windows)
venv\Scripts\activate
# Aktivasi virtual environment (Linux/MacOS)
source venv/bin/activate
```

### 3. Instalasi Dependensi
```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment Variables (`.env`)
Buat berkas `.env` pada root direktori (atau salin dari `.env.example`):

```env
# Google Gemini AI API Key (Dapatkan di Google AI Studio)
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere...

# MongoDB Atlas Connection URI
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority

# Database Configuration
DB_NAME=smart_meal_db
COLLECTION_NAME=meal_plans
```

> 💡 **Informasi Resilience**: Jika `GEMINI_API_KEY` atau `MONGODB_URI` dikosongkan saat pengujian lokal, sistem akan secara otomatis beralih ke *Intelligent Fallback Generator* & *In-Memory Store* tanpa memicu error/crash.

### 5. Jalankan Server Lokal
```bash
python -m uvicorn app.main:app --reload
```

Server akan aktif dan siap diakses melalui browser di:
* **GUI QA Chat Assistant Studio**: `http://localhost:8000`
* **Dokumentasi Swagger API**: `http://localhost:8000/docs`

---

## 📡 Dokumentasi Endpoint API

### 1. Jalankan Pengujian Integrasi (`POST /api/v1/test-integration`)

Memicu eksekusi 3 Micro-Agents untuk menguji target endpoint API.

#### Request Example:
```json
POST /api/v1/test-integration
Content-Type: application/json

{
  "target_endpoint": "https://jsonplaceholder.typicode.com/posts",
  "scenario_description": "Uji validasi pengiriman data postingan baru dengan variasi payload valid, data besar, dan payload invalid"
}
```

#### Response Example (200 OK):
```json
{
  "status": "SUCCESS",
  "agent_logs": {
    "generated_test_cases": [
      {
        "case_type": "Positif (Valid Payload)",
        "payload_data": {
          "title": "Skenario Uji Integrasi Valid",
          "body": "Eksekusi skenario uji otomatis...",
          "userId": 1,
          "status": "active"
        },
        "expected_behavior": "HTTP 200 OK / 201 Created — Endpoint merespons dengan sukses & struktur data valid."
      }
    ],
    "execution_results": [
      {
        "case_type": "Positif (Valid Payload)",
        "target_url": "https://jsonplaceholder.typicode.com/posts",
        "http_method": "POST",
        "status_code": 201,
        "latency_ms": 142.5,
        "is_success": true,
        "response_snippet": "{\n  \"title\": \"Skenario Uji Integrasi Valid\",\n  \"id\": 101\n}"
      }
    ]
  },
  "llm_evaluation": {
    "integration_health_score": 95,
    "summary": "Pengujian integrasi endpoint https://jsonplaceholder.typicode.com/posts selesai dieksekusi dengan passing rate 100% dan latensi rata-rata 142.5 ms.",
    "root_cause_analysis": [
      "Tidak ditemukan kegagalan kritis pada layer controller."
    ],
    "recommendations": [
      "Tambahkan skema validasi Pydantic pada layer API controller.",
      "Implementasikan caching untuk mengoptimalkan latensi di bawah 100 ms."
    ],
    "report_md": "# 📑 Laporan Hasil Pengujian Integrasi Microservices\n\n### 🎯 Detail Skenario Uji\n- **Target Endpoint**: `https://jsonplaceholder.typicode.com/posts`..."
  },
  "local_files": {
    "json_filepath": "app/output/raw_json/test_run_20260724_130054_0f327a9f.json",
    "md_filepath": "app/output/reports/test_report_20260724_130054_0f327a9f.md"
  },
  "saved_id": "0f327a9f",
  "created_at": "24 Jul 2026, 13:00"
}
```

---

### 2. Ambil Riwayat Pengujian (`GET /api/v1/history`)

Mengambil daftar riwayat pengujian yang pernah dieksekusi dari database MongoDB Atlas / In-Memory Store.

#### Request Example:
```bash
GET /api/v1/history?limit=10
```

#### Response Example (200 OK):
```json
{
  "status": "SUCCESS",
  "count": 1,
  "data": [
    {
      "id": "0f327a9f",
      "created_at": "24 Jul 2026, 13:00",
      "request_payload": {
        "target_endpoint": "https://jsonplaceholder.typicode.com/posts",
        "scenario_description": "Uji validasi pengiriman postingan baru"
      },
      "llm_evaluation": {
        "integration_health_score": 95,
        "summary": "Pengujian integrasi berhasil dieksekusi..."
      }
    }
  ]
}
```

---

## 📂 Struktur Direktori Proyek

```text
agentic-integration-testing/
├── api/
│   └── index.py               # Entrypoint Vercel Serverless Function
├── app/
│   ├── __init__.py
│   ├── main.py                # Aplikasi FastAPI, Endpoint Routes, & Static Mount
│   ├── core/
│   │   ├── config.py          # Pemuat Environment Variables (Dotenv)
│   │   └── database.py        # Driver Async MongoDB (Motor) & Local File Saver
│   ├── schemas/
│   │   ├── test_schema.py     # Kontrak Model Pydantic (Request, Logs, LLM Output)
│   │   └── meal_schema.py     # Re-export Alias & Schemas
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── generator_agent.py # Agent 1: Test Suite Generator (Deterministik)
│   │   ├── executor_agent.py  # Agent 2: Test Execution Runner (Async HTTPX)
│   │   ├── evaluator_agent.py # Agent 3: Master Evaluator (Gemini LLM Aggregator)
│   │   └── chef_agent.py      # Re-export Alias Agent 3
│   └── output/                # Otomatisasi Direktori File Tersimpan
│       ├── raw_json/          # Berkas Output Mentah Berformat JSON (.json)
│       └── reports/           # Berkas Laporan Evaluasi Berformat Markdown (.md)
├── public/
│   ├── index.html             # Conversational AI QA Chat UI & Marked.js Integration
│   ├── app.js                 # Chat Engine, Blob Downloader, & Auto URL Cleaner
│   └── style.css              # Custom Styling (Royal & Ice Blue Palette)
├── .env                       # File Rahasia Variabel Lingkungan (Keys & URIs)
├── .env.example               # Template Variabel Lingkungan
├── .gitignore                 # Daftar File yang Diabaikan oleh Git
├── requirements.txt           # Lockfile Dependensi Python
├── vercel.json                # Konfigurasi Build & Routing Vercel Serverless
└── README.md                  # Dokumentasi Resmi Repositori Proyek
```

---

## 📄 Lisensi & Hak Cipta

Dikembangkan untuk kebutuhan **Tugas Akademik & Software Engineering Agentic Integration Testing**. Bebas digunakan, dimodifikasi, dan didistribusikan di bawah lisensi open-source MIT.
