import json
from fastapi import APIRouter, Request, Depends, Form, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.config import settings
from app.database import get_session
from app.models import StudentSubmission, AIEvaluation, User
from app.routers.auth import require_teacher, require_super_user
from app.routers.student import _regrade_submission

router = APIRouter(prefix="/teacher")
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def dashboard(
    request: Request,
    session: Session = Depends(get_session),
):
    if settings.google_oauth_enabled:
        user = require_teacher(request, session)
    else:
        user = {"role": "super_user"}

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
        "user": user,
        "is_super_user": user.get("role") == "super_user",
        "oauth_enabled": settings.google_oauth_enabled,
    })


@router.get("/users")
async def user_list(
    request: Request,
    session: Session = Depends(get_session),
):
    if not settings.google_oauth_enabled:
        return RedirectResponse(url="/teacher", status_code=303)

    user = require_super_user(request, session)
    users = session.exec(select(User).order_by(User.created_at.desc())).all()
    return templates.TemplateResponse("teacher_users.html", {
        "request": request,
        "users": users,
        "user": user,
        "oauth_enabled": settings.google_oauth_enabled,
        "is_super_user": True,
        "super_user_email": settings.super_user_email,
    })


@router.post("/users/{target_user_id}/promote")
async def promote_user_to_teacher(
    request: Request,
    target_user_id: str,
    session: Session = Depends(get_session),
):
    if not settings.google_oauth_enabled:
        return RedirectResponse(url="/teacher", status_code=303)

    require_super_user(request, session)
    target = session.get(User, target_user_id)
    if target and target.role == "student":
        target.role = "teacher"
        session.add(target)
        session.commit()
    return RedirectResponse(url="/teacher/users", status_code=303)


@router.get("/{submission_id}")
async def review(
    request: Request,
    submission_id: str,
    session: Session = Depends(get_session),
):
    if settings.google_oauth_enabled:
        user = require_teacher(request, session)
    else:
        user = {"role": "super_user"}

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
        "user": user,
        "is_super_user": user.get("role") == "super_user",
        "oauth_enabled": settings.google_oauth_enabled,
    })


@router.post("/{submission_id}/override")
async def override_comment(
    request: Request,
    submission_id: str,
    teacher_comment: str = Form(...),
    session: Session = Depends(get_session),
):
    if settings.google_oauth_enabled:
        require_teacher(request, session)

    evaluation = session.exec(
        select(AIEvaluation).where(AIEvaluation.submission_id == submission_id)
    ).first()

    if evaluation:
        evaluation.teacher_override = teacher_comment
        evaluation.reviewed_by_teacher = True
        session.add(evaluation)
        session.commit()

    return RedirectResponse(url=f"/teacher/{submission_id}", status_code=303)


@router.post("/{submission_id}/regrade")
async def regrade_submission(
    request: Request,
    submission_id: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    if settings.google_oauth_enabled:
        require_teacher(request, session)

    submission = session.get(StudentSubmission, submission_id)
    if not submission:
        return RedirectResponse(url="/teacher", status_code=303)
    if submission.status == "grading":
        return RedirectResponse(url=f"/teacher/{submission_id}", status_code=303)

    evaluation = session.exec(
        select(AIEvaluation).where(AIEvaluation.submission_id == submission_id)
    ).first()

    if submission.status == "error":
        if not evaluation:
            return RedirectResponse(url=f"/teacher/{submission_id}", status_code=303)
    elif submission.status == "completed":
        if not evaluation or not evaluation.reviewed_by_teacher:
            return RedirectResponse(url=f"/teacher/{submission_id}", status_code=303)
    else:
        return RedirectResponse(url=f"/teacher/{submission_id}", status_code=303)

    submission.status = "grading"
    session.add(submission)
    session.commit()
    background_tasks.add_task(_regrade_submission, submission_id)
    return RedirectResponse(url=f"/teacher/{submission_id}", status_code=303)
