# Re-export integration test schemas for backward compatibility
from app.schemas.test_schema import (
    IntegrationTestRequest,
    TestCasePayload,
    ExecutionResultLog,
    LLMEvaluationOutput,
    AgentExecutionLogs,
    TestRunResultResponse
)

# Aliases for compatibility
MealPlannerPayload = IntegrationTestRequest
MealPlannerResponse = TestRunResultResponse
