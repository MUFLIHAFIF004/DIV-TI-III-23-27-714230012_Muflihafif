import sys
import os

# Ensure workspace root directory is at the top of sys.path for Uvicorn imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.schemas.test_schema import (
    IntegrationTestRequest,
    TestRunResultResponse,
    AgentExecutionLogs,
    LocalOutputFiles
)
from app.agents.generator_agent import generate_test_suite
from app.agents.executor_agent import execute_test_suite
from app.agents.evaluator_agent import evaluate_test_results
from app.core.database import save_meal_plan, get_meal_history, save_local_output_files

app = FastAPI(
    title="Agentic Integration Testing System API",
    description="Micro-Agentic Architecture for Automated Integration Testing & Evaluation using FastAPI, 1 Gemini LLM, & MongoDB Atlas",
    version="3.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Agentic Integration Testing System",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/test-integration", response_model=TestRunResultResponse)
@app.post("/api/v1/plan-meal", response_model=TestRunResultResponse)
async def test_integration_pipeline(payload: IntegrationTestRequest):
    try:
        # Step 1: Agent 1 - Test Suite Generator (Deterministic Python)
        test_cases = generate_test_suite(payload)

        # Step 2: Agent 2 - Test Execution Runner (Python Async / HTTPX)
        execution_results = await execute_test_suite(test_cases, payload.target_endpoint)

        # Step 3: Agent 3 - Master Evaluator Agent (Gemini LLM Aggregator)
        llm_evaluation = await evaluate_test_results(payload, test_cases, execution_results)

        agent_logs = AgentExecutionLogs(
            generated_test_cases=test_cases,
            execution_results=execution_results
        )

        now_str = datetime.now().strftime("%d %b %Y, %H:%M")

        # Document structure for DB persistence & local output file creation
        document = {
            "created_at": now_str,
            "request_payload": payload.model_dump(),
            "agent_logs": agent_logs.model_dump(),
            "llm_evaluation": llm_evaluation.model_dump()
        }

        # Step 4: Persist to MongoDB Atlas & local app/output files
        saved_id = await save_meal_plan(document)
        local_files_dict = save_local_output_files(document, saved_id)

        local_files = LocalOutputFiles(
            json_filepath=local_files_dict["json_filepath"],
            md_filepath=local_files_dict["md_filepath"]
        )

        return TestRunResultResponse(
            status="SUCCESS",
            agent_logs=agent_logs,
            llm_evaluation=llm_evaluation,
            local_files=local_files,
            saved_id=saved_id,
            created_at=now_str
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses pengujian integrasi: {str(e)}")

@app.get("/api/v1/history")
async def fetch_history(limit: int = 10):
    try:
        history = await get_meal_history(limit=limit)
        return {
            "status": "SUCCESS",
            "count": len(history),
            "data": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil riwayat pengujian: {str(e)}")

# Mount static frontend files directly at root "/" so style.css and app.js are served properly
public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if os.path.exists(public_dir):
    app.mount("/", StaticFiles(directory=public_dir, html=True), name="static")
