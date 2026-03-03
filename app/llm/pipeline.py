import json
from dataclasses import dataclass
from app.llm.client import OllamaClient
from app.llm.gemini_client import GeminiClient
from app.llm.prompts import build_stage1_prompt, build_stage2_prompt, build_stage3_prompt


@dataclass
class GradingResult:
    student_self_reflection: dict
    teacher_scores: dict
    teacher_comment: str
    raw_output: dict


class GradingPipeline:
    def __init__(self, client: OllamaClient, questionnaires: dict, gemini_client: GeminiClient | None = None):
        self.client = client
        self.questionnaires = questionnaires
        self.gemini_client = gemini_client

    async def grade(self, questionnaire_id: str, student_answer: dict) -> GradingResult:
        questionnaire = self.questionnaires[questionnaire_id]

        # Stage 1 & 2: Always use Ollama (structured JSON output)
        system1, prompt1 = build_stage1_prompt(questionnaire, student_answer)
        understanding = await self.client.generate(prompt1, system=system1)

        system2, prompt2 = build_stage2_prompt(questionnaire, student_answer, understanding)
        evaluation = await self.client.generate(prompt2, system=system2)

        # Stage 3: Use Gemini if available, otherwise Ollama
        system3, prompt3 = build_stage3_prompt(questionnaire, student_answer, evaluation)
        if self.gemini_client:
            comment = await self.gemini_client.generate_text(prompt3, system=system3)
            stage3_engine = "gemini"
        else:
            comment = await self.client.generate_text(prompt3, system=system3)
            stage3_engine = "ollama"

        return GradingResult(
            student_self_reflection=evaluation.get("student_self_reflection", {}),
            teacher_scores=evaluation.get("teacher_feedback", {}),
            teacher_comment=comment,
            raw_output={
                "stage1_understanding": understanding,
                "stage2_evaluation": evaluation,
                "stage3_comment": comment,
                "stage3_engine": stage3_engine,
            },
        )
