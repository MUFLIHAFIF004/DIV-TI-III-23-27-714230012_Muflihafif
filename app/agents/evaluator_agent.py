import re
import json
import logging
from typing import List, Dict, Any
from app.core.config import settings
from app.schemas.test_schema import (
    IntegrationTestRequest,
    TestCasePayload,
    ExecutionResultLog,
    LLMEvaluationOutput
)

logger = logging.getLogger("agentic_testing.evaluator_agent")

def _parse_llm_json_response(raw_text: str) -> Dict[str, Any]:
    """Extracts valid JSON object from LLM response text safely."""
    if not raw_text or not raw_text.strip():
        raise ValueError("Empty response text from LLM")
    
    text = raw_text.strip()
    
    # Try finding first '{' and last '}'
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except Exception:
            # Clean control characters / unescaped newlines inside strings
            sanitized = re.sub(r'[\r\n\t]', ' ', json_str)
            return json.loads(sanitized)
    
    return json.loads(text)

async def evaluate_test_results(
    request: IntegrationTestRequest,
    test_cases: List[TestCasePayload],
    execution_results: List[ExecutionResultLog]
) -> LLMEvaluationOutput:
    """
    Micro-Agent 3: Master Evaluator Agent (Gemini LLM Aggregator - High Reliability)
    Consolidates logs from Agent 1 & 2. Asks Gemini for fast concise metrics, then assembles a complete Markdown report.
    """
    api_key = (settings.GEMINI_API_KEY or "").strip()

    # Calculate preliminary execution metrics deterministically (0 ms)
    total_cases = len(execution_results)
    passed_cases = sum(1 for r in execution_results if r.is_success)
    pass_rate = round((passed_cases / max(1, total_cases)) * 100, 1)
    avg_latency = round(sum(r.latency_ms for r in execution_results) / max(1, total_cases), 2)

    # Check if API Key is empty or placeholder template
    if not api_key or "your_" in api_key.lower() or len(api_key) < 10:
        logger.info("GEMINI_API_KEY not configured. Using intelligent default LLM evaluator.")
        return _generate_fallback_evaluation(request, test_cases, execution_results, pass_rate, avg_latency)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Prepare compact test log summary for fast LLM reasoning
        cases_summary = []
        for tc, res in zip(test_cases, execution_results):
            status = 'PASSED' if res.is_success else 'FAILED'
            cases_summary.append(f"- Case [{tc.case_type}]: Status {res.status_code}, Latency {res.latency_ms}ms, Result {status}")

        prompt = f"""
System: Anda adalah Senior QA Automation Architect.
Tugas: Evaluasi ringkas hasil pengujian API berikut.

Target Endpoint: {request.target_endpoint}
Skenario Uji: {request.scenario_description}
Passing Rate: {pass_rate}% ({passed_cases}/{total_cases} Lulus)
Rata-rata Latensi: {avg_latency} ms

[LOG PENGUJIAN]
{chr(10).join(cases_summary)}

Keluarkan HANYA JSON valid sesuai struktur berikut:
{{
  "integration_health_score": {int(pass_rate)},
  "summary": "Ringkasan evaluasi singkat dalam 2 kalimat.",
  "root_cause_analysis": [
    "Analisis utama hasil pengujian"
  ],
  "recommendations": [
    "Rekomendasi perbaikan 1",
    "Rekomendasi perbaikan 2"
  ]
}}
"""

        model_name = "gemini-2.5-flash"

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=350,
                response_mime_type="application/json"
            )
        )

        data = _parse_llm_json_response(response.text)

        summary = data.get("summary", f"Skenario integrasi selesai dengan passing rate {pass_rate}% dan latensi {avg_latency} ms.")
        root_causes = data.get("root_cause_analysis", ["Validasi endpoint merespons sesuai skenario pengujian."])
        recommendations = data.get("recommendations", ["Implementasikan skema validasi Pydantic dan caching."])
        health_score = int(data.get("integration_health_score", int(pass_rate)))

        # Assemble full, beautifully formatted Markdown report in Python (0 ms)
        report_md = _build_default_markdown_report(
            request,
            execution_results,
            pass_rate,
            avg_latency,
            summary,
            root_causes,
            recommendations
        )

        return LLMEvaluationOutput(
            integration_health_score=health_score,
            summary=summary,
            root_cause_analysis=root_causes,
            recommendations=recommendations,
            report_md=report_md
        )

    except Exception as e:
        logger.error(f"Error calling Gemini AI for evaluator: {e}. Utilizing fallback evaluation builder.")
        return _generate_fallback_evaluation(request, test_cases, execution_results, pass_rate, avg_latency)

def _generate_fallback_evaluation(
    request: IntegrationTestRequest,
    test_cases: List[TestCasePayload],
    execution_results: List[ExecutionResultLog],
    pass_rate: float,
    avg_latency: float
) -> LLMEvaluationOutput:
    """Offline default evaluator generator when Gemini API key is unconfigured or unavailable."""
    score = int(pass_rate)
    summary = f"Pengujian integrasi endpoint {request.target_endpoint} selesai dieksekusi dengan passing rate {pass_rate}% dan rata-rata latensi {avg_latency} ms."

    root_causes = []
    for r in execution_results:
        if not r.is_success:
            root_causes.append(f"Kasus {r.case_type} mengembalikan HTTP Status {r.status_code} ({r.response_snippet[:80]}...).")

    if not root_causes:
        root_causes.append("Tidak ditemukan kegagalan kritis. Seluruh skenario batas dan validasi ditangani dengan aman.")

    recommendations = [
        "Tambahkan skema validasi Pydantic / OpenAPI pada layer controller microservice.",
        "Implementasikan caching atau indeks database untuk mengoptimalkan waktu respons di bawah 200 ms.",
        "Lakukan pengujian beban (load test) secara berkelanjutan menggunakan pipeline CI/CD."
    ]

    report_md = _build_default_markdown_report(request, execution_results, pass_rate, avg_latency, summary, root_causes, recommendations)

    return LLMEvaluationOutput(
        integration_health_score=score,
        summary=summary,
        root_cause_analysis=root_causes,
        recommendations=recommendations,
        report_md=report_md
    )

def _build_default_markdown_report(
    request: IntegrationTestRequest,
    execution_results: List[ExecutionResultLog],
    pass_rate: float,
    avg_latency: float,
    summary: str,
    root_causes: List[str] = None,
    recommendations: List[str] = None
) -> str:
    """Utility to generate rich Markdown text for GUI visual rendering via Marked.js instantly."""
    rows = []
    for res in execution_results:
        badge = "✅ **LULUS**" if res.is_success else "❌ **GAGAL**"
        rows.append(f"| `{res.case_type}` | `{res.http_method}` | **{res.status_code}** | {res.latency_ms} ms | {badge} |")

    table_body = "\n".join(rows)

    rc_list = "\n".join([f"- {rc}" for rc in (root_causes or ["Validasi berjalan sesuai ekspektasi."])])
    rec_list = "\n".join([f"- {rec}" for rec in (recommendations or ["Pertahankan validasi data."])])

    return f"""# 📑 Laporan Hasil Pengujian Integrasi Microservices

### 🎯 Detail Skenario Uji
- **Target Endpoint**: `{request.target_endpoint}`
- **Deskripsi Skenario**: {request.scenario_description}
- **Passing Rate**: **{pass_rate}%**
- **Rata-rata Latensi**: **{avg_latency} ms**

---

### 📊 Tabel Eksekusi Test Cases (Agent 1 & Agent 2)

| Tipe Test Case | Method | Status Code | Latensi (ms) | Hasil Pengujian |
| :--- | :---: | :---: | :---: | :---: |
{table_body}

---

### 🔎 Ringkasan Evaluasi (Agent 3 - Gemini AI)
{summary}

### ⚠️ Analisis Akar Masalah (Root Cause)
{rc_list}

### 🛡️ Rekomendasi Perbaikan Developer
{rec_list}
"""
