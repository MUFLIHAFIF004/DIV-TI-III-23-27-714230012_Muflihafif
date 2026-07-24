import time
import json
import logging
from typing import List
from app.schemas.test_schema import TestCasePayload, ExecutionResultLog

logger = logging.getLogger("agentic_testing.executor_agent")

async def execute_test_suite(test_cases: List[TestCasePayload], target_endpoint: str) -> List[ExecutionResultLog]:
    """
    Micro-Agent 2: Test Execution Runner (Python Async / HTTPX)
    Executes live HTTP API calls asynchronously, records HTTP status codes, latency in ms, and response snippets.
    """
    execution_results: List[ExecutionResultLog] = []

    try:
        import httpx
        use_httpx = True
    except ImportError:
        use_httpx = False
        logger.warning("httpx package not installed. Utilizing standard library fallback for execution runner.")

    for test_case in test_cases:
        case_type = test_case.case_type
        payload = test_case.payload_data
        start_time = time.perf_counter()

        status_code = 0
        response_snippet = ""
        is_success = False

        if use_httpx:
            try:
                async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                    response = await client.post(
                        target_endpoint,
                        json=payload,
                        headers={"Content-Type": "application/json", "User-Agent": "Agentic-Integration-Test-Runner/1.0"}
                    )
                    end_time = time.perf_counter()
                    latency_ms = round((end_time - start_time) * 1000, 2)
                    status_code = response.status_code
                    response_snippet = response.text[:300]
            except Exception as e:
                end_time = time.perf_counter()
                latency_ms = round((end_time - start_time) * 1000, 2)
                status_code = 503  # Service Unavailable / Connection Error
                response_snippet = f"Error Koneksi Endpoint: {str(e)}"
        else:
            # Fallback using urllib standard library synchronously wrapped
            try:
                import urllib.request
                import urllib.error
                req = urllib.request.Request(
                    target_endpoint,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={"Content-Type": "application/json", "User-Agent": "Agentic-Test-Runner/1.0"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    end_time = time.perf_counter()
                    latency_ms = round((end_time - start_time) * 1000, 2)
                    status_code = resp.getcode()
                    response_snippet = resp.read().decode('utf-8', errors='ignore')[:300]
            except urllib.error.HTTPError as he:
                end_time = time.perf_counter()
                latency_ms = round((end_time - start_time) * 1000, 2)
                status_code = he.code
                response_snippet = he.read().decode('utf-8', errors='ignore')[:300]
            except Exception as ex:
                end_time = time.perf_counter()
                latency_ms = round((end_time - start_time) * 1000, 2)
                status_code = 500
                response_snippet = f"Execution Failure: {str(ex)}"

        # Evaluate success condition based on test case expectations
        if "Positif" in case_type:
            is_success = (200 <= status_code < 300)
        elif "Negatif" in case_type:
            is_success = (400 <= status_code < 500)
        elif "Edge" in case_type:
            is_success = (200 <= status_code < 500) and (status_code != 500)

        execution_results.append(
            ExecutionResultLog(
                case_type=case_type,
                target_url=target_endpoint,
                http_method="POST",
                status_code=status_code,
                latency_ms=latency_ms,
                is_success=is_success,
                response_snippet=response_snippet
            )
        )

    return execution_results
