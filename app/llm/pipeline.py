import json
from dataclasses import dataclass
from app.llm.client import OllamaClient
from app.llm.prompts import build_stage1_prompt, build_stage2_prompt, build_stage3_prompt


@dataclass
class GradingResult:
    student_self_reflection: dict
    teacher_scores: dict
    teacher_comment: str
    raw_output: dict


class GradingPipeline:
    def __init__(self, client: OllamaClient, questionnaires: dict):
        self.client = client
        self.questionnaires = questionnaires

    async def grade(self, questionnaire_id: str, student_answer: dict) -> GradingResult:
        questionnaire = self.questionnaires[questionnaire_id]

        system1, prompt1 = build_stage1_prompt(questionnaire, student_answer)
        understanding = await self.client.generate(prompt1, system=system1)

        system2, prompt2 = build_stage2_prompt(questionnaire, student_answer, understanding)
        evaluation = await self.client.generate(prompt2, system=system2)

        system3, prompt3 = build_stage3_prompt(questionnaire, student_answer, evaluation)
        comment = await self.client.generate_text(prompt3, system=system3)

        return GradingResult(
            student_self_reflection=evaluation.get("student_self_reflection", {}),
            teacher_scores=evaluation.get("teacher_feedback", {}),
            teacher_comment=comment,
            raw_output={
                "stage1_understanding": understanding,
                "stage2_evaluation": evaluation,
                "stage3_comment": comment,
            },
        )
