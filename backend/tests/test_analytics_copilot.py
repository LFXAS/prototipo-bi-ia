from app.modules.analytics.router import _ANALYTICS_COPILOT_INSTRUCTION
from app.modules.analytics.schemas import AnalyticsCopilotRequest


def test_analytics_copilot_normalizes_question_and_limits_history() -> None:
    payload = AnalyticsCopilotRequest(
        question="  ¿Qué   resultado   debería revisar primero?  ",
        history=[],
        execution_id=7,
    )

    assert payload.question == "¿Qué resultado debería revisar primero?"
    assert payload.execution_id == 7


def test_analytics_copilot_instruction_separates_observation_from_causes() -> None:
    instruction = _ANALYTICS_COPILOT_INSTRUCTION.casefold()

    assert "no inventes cifras, causas" in instruction
    assert "nunca enumeres causas hipotéticas" in instruction
    assert "no generes sql" in instruction
