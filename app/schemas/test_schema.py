from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class IntegrationTestRequest(BaseModel):
    target_endpoint: str = Field(..., description="URL endpoint API microservice yang akan diuji", example="https://jsonplaceholder.typicode.com/posts")
    scenario_description: str = Field(..., description="Deskripsi skenario pengujian integrasi dari user", example="Uji validasi pengiriman data postingan baru dengan payload normal dan data berukuran besar")

class TestCasePayload(BaseModel):
    case_type: str = Field(..., description="Tipe pengujian: Positif, Edge Case, atau Negatif")
    payload_data: Dict[str, Any] = Field(default_factory=dict, description="Payload data JSON yang dikirimkan ke target endpoint")
    expected_behavior: str = Field(..., description="Ekspektasi perilaku sistem / HTTP Status Code")

class ExecutionResultLog(BaseModel):
    case_type: str
    target_url: str
    http_method: str = "POST"
    status_code: int
    latency_ms: float
    is_success: bool
    response_snippet: str

class LLMEvaluationOutput(BaseModel):
    integration_health_score: int = Field(..., description="Skor kesehatan integrasi (0 - 100%)", example=95)
    summary: str = Field(..., description="Ringkasan hasil evaluasi pengujian integrasi")
    root_cause_analysis: List[str] = Field(default_factory=list, description="Daftar analisis akar masalah jika ada kesalahan")
    recommendations: List[str] = Field(default_factory=list, description="Rekomendasi perbaikan untuk developer")
    report_md: str = Field(..., description="Laporan analisis teknis lengkap dalam format Markdown (MD)")

class AgentExecutionLogs(BaseModel):
    generated_test_cases: List[TestCasePayload]
    execution_results: List[ExecutionResultLog]

class LocalOutputFiles(BaseModel):
    json_filepath: str = Field(..., description="Path file lokasi tersimpannya raw output JSON")
    md_filepath: str = Field(..., description="Path file lokasi tersimpannya laporan Markdown")

class TestRunResultResponse(BaseModel):
    status: str = "SUCCESS"
    agent_logs: AgentExecutionLogs
    llm_evaluation: LLMEvaluationOutput
    local_files: Optional[LocalOutputFiles] = None
    saved_id: Optional[str] = None
    created_at: Optional[str] = None
