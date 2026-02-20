import json
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.models import StudentSubmission, AIEvaluation

router = APIRouter(prefix="/teacher")
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def dashboard(request: Request, session: Session = Depends(get_session)):
    from app.main import app_state
    submissions = session.exec(
        select(StudentSubmission).order_by(StudentSubmission.created_at.desc())
    ).all()

    enriched = []
    for sub in submissions:
        ev = session.exec(
            select(AIEvaluation).where(AIEvaluation.submission_id == sub.id)
        ).first()
        q_name = app_state["questionnaires"].get(sub.questionnaire_id, {}).get("name", sub.questionnaire_id)
        overall = ""
        if ev:
            try:
                scores = json.loads(ev.teacher_scores)
                overall = scores.get("overall_quality", "")
            except (json.JSONDecodeError, AttributeError):
                pass
        enriched.append({
            "submission": sub,
            "questionnaire_name": q_name,
            "overall_quality": overall,
            "reviewed": ev.reviewed_by_teacher if ev else False,
        })

    return templates.TemplateResponse("teacher_dashboard.html", {
        "request": request,
        "submissions": enriched,
    })


@router.get("/{submission_id}")
async def review(request: Request, submission_id: str, session: Session = Depends(get_session)):
    from app.main import app_state
    submission = session.get(StudentSubmission, submission_id)
    if not submission:
        return RedirectResponse(url="/teacher")

    evaluation = session.exec(
        select(AIEvaluation).where(AIEvaluation.submission_id == submission_id)
    ).first()

    answers = json.loads(submission.raw_answer)
    q_name = app_state["questionnaires"].get(submission.questionnaire_id, {}).get("name", submission.questionnaire_id)

    self_reflection = {}
    scores = {}
    if evaluation:
        try:
            self_reflection = json.loads(evaluation.student_self_reflection) if evaluation.student_self_reflection else {}
        except json.JSONDecodeError:
            pass
        try:
            scores = json.loads(evaluation.teacher_scores) if evaluation.teacher_scores else {}
        except json.JSONDecodeError:
            pass

    return templates.TemplateResponse("teacher_review.html", {
        "request": request,
        "submission": submission,
        "evaluation": evaluation,
        "answers": answers,
        "questionnaire_name": q_name,
        "self_reflection": self_reflection,
        "scores": scores,
    })


@router.post("/{submission_id}/override")
async def override_comment(
    submission_id: str,
    teacher_comment: str = Form(...),
    session: Session = Depends(get_session),
):
    evaluation = session.exec(
        select(AIEvaluation).where(AIEvaluation.submission_id == submission_id)
    ).first()

    if evaluation:
        evaluation.teacher_override = teacher_comment
        evaluation.reviewed_by_teacher = True
        session.add(evaluation)
        session.commit()

    return RedirectResponse(url=f"/teacher/{submission_id}", status_code=303)
