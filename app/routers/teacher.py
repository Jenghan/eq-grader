import json
from pathlib import Path
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


def _can_view_submission(user: dict, submission: StudentSubmission) -> bool:
    if user.get("role") == "super_user":
        return True
    if user.get("role") == "teacher":
        return submission.assigned_teacher_id == user.get("id")
    return False


def _list_assignable_teachers(session: Session) -> list[User]:
    users = session.exec(select(User)).all()
    cand = [u for u in users if u.role in {"teacher", "super_user"}]
    cand.sort(key=lambda u: ((u.name or u.email or "").lower(), (u.email or "").lower()))
    return cand


def _list_log_files() -> list[str]:
    log_dir = Path(settings.log_dir)
    if not log_dir.exists():
        return []
    files = [p.name for p in log_dir.glob(f"{settings.log_file_name}*") if p.is_file()]
    files.sort(reverse=True)
    return files


@router.get("")
async def dashboard(
    request: Request,
    session: Session = Depends(get_session),
):
    if settings.google_oauth_enabled:
        user = require_teacher(request, session)
    else:
        user = {"role": "super_user", "id": None}

    from app.main import app_state
    all_rows = session.exec(
        select(StudentSubmission).order_by(StudentSubmission.created_at.desc())
    ).all()

    if user.get("role") == "super_user":
        submissions = all_rows
    else:
        submissions = [s for s in all_rows if s.assigned_teacher_id == user.get("id")]

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
        assignee = None
        if sub.assigned_teacher_id:
            assignee = session.get(User, sub.assigned_teacher_id)
        enriched.append({
            "submission": sub,
            "questionnaire_name": q_name,
            "overall_quality": overall,
            "reviewed": ev.reviewed_by_teacher if ev else False,
            "assignee": assignee,
        })

    reviewer_options = _list_assignable_teachers(session) if user.get("role") == "super_user" else []

    return templates.TemplateResponse("teacher_dashboard.html", {
        "request": request,
        "submissions": enriched,
        "user": user,
        "is_super_user": user.get("role") == "super_user",
        "oauth_enabled": settings.google_oauth_enabled,
        "reviewer_options": reviewer_options,
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


@router.get("/logs")
async def logs_viewer(
    request: Request,
    file: str | None = None,
    page: int = 1,
    per_page: int = 100,
    session: Session = Depends(get_session),
):
    if not settings.google_oauth_enabled:
        return RedirectResponse(url="/teacher", status_code=303)

    user = require_super_user(request, session)
    log_files = _list_log_files()
    if not log_files:
        return templates.TemplateResponse("teacher_logs.html", {
            "request": request,
            "user": user,
            "is_super_user": True,
            "oauth_enabled": settings.google_oauth_enabled,
            "log_files": [],
            "selected_file": None,
            "page": 1,
            "per_page": per_page,
            "total_pages": 1,
            "total_lines": 0,
            "entries": [],
        })

    selected_file = file if file in log_files else log_files[0]
    log_path = Path(settings.log_dir) / selected_file
    if not log_path.exists():
        selected_file = log_files[0]
        log_path = Path(settings.log_dir) / selected_file

    per_page = max(20, min(per_page, 300))
    page = max(1, page)

    try:
        all_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        all_lines = []

    # Show newest entries first.
    all_lines.reverse()
    total_lines = len(all_lines)
    total_pages = max((total_lines + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages
    start = (page - 1) * per_page
    end = start + per_page
    entries = all_lines[start:end]

    return templates.TemplateResponse("teacher_logs.html", {
        "request": request,
        "user": user,
        "is_super_user": True,
        "oauth_enabled": settings.google_oauth_enabled,
        "log_files": log_files,
        "selected_file": selected_file,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "total_lines": total_lines,
        "entries": entries,
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


@router.post("/submissions/batch-assign")
async def batch_assign_submissions(
    request: Request,
    session: Session = Depends(get_session),
):
    if not settings.google_oauth_enabled:
        return RedirectResponse(url="/teacher", status_code=303)

    require_super_user(request, session)
    form = await request.form()
    submission_ids = form.getlist("submission_ids")
    teacher_id = (form.get("assign_teacher_id") or "").strip()

    if not submission_ids or not teacher_id:
        return RedirectResponse(url="/teacher?error=batch_assign_incomplete", status_code=303)

    assignee = session.get(User, teacher_id)
    if not assignee or assignee.role not in {"teacher", "super_user"}:
        return RedirectResponse(url="/teacher?error=batch_assign_invalid_teacher", status_code=303)

    for sid in submission_ids:
        sub = session.get(StudentSubmission, sid)
        if sub:
            sub.assigned_teacher_id = teacher_id
            session.add(sub)
    session.commit()
    return RedirectResponse(url="/teacher?batch_assigned=1", status_code=303)


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

    if not _can_view_submission(user, submission):
        return RedirectResponse(url="/teacher?error=not_assignee", status_code=303)

    assignee = None
    if submission.assigned_teacher_id:
        assignee = session.get(User, submission.assigned_teacher_id)

    evaluation = session.exec(
        select(AIEvaluation).where(AIEvaluation.submission_id == submission_id)
    ).first()

    answers = json.loads(submission.raw_answer)
    q_name = app_state["questionnaires"].get(submission.questionnaire_id, {}).get("name", submission.questionnaire_id)

    self_reflection = {}
    scores = {}
    error_detail = ""
    if evaluation:
        try:
            self_reflection = json.loads(evaluation.student_self_reflection) if evaluation.student_self_reflection else {}
        except json.JSONDecodeError:
            pass
        try:
            scores = json.loads(evaluation.teacher_scores) if evaluation.teacher_scores else {}
        except json.JSONDecodeError:
            pass
        if submission.status == "error" and evaluation.raw_llm_output:
            try:
                raw = json.loads(evaluation.raw_llm_output)
                if isinstance(raw, dict):
                    tb = raw.get("traceback", "")
                    err = raw.get("error", "")
                    error_detail = tb or err or evaluation.raw_llm_output
                else:
                    error_detail = str(raw)
            except json.JSONDecodeError:
                error_detail = evaluation.raw_llm_output

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
        "assignee": assignee,
        "error_detail": error_detail,
    })


@router.post("/{submission_id}/override")
async def override_comment(
    request: Request,
    submission_id: str,
    teacher_comment: str = Form(...),
    session: Session = Depends(get_session),
):
    if settings.google_oauth_enabled:
        user = require_teacher(request, session)
    else:
        user = {"role": "super_user", "id": None}

    submission = session.get(StudentSubmission, submission_id)
    if not submission or not _can_view_submission(user, submission):
        return RedirectResponse(url="/teacher?error=not_assignee", status_code=303)

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
        user = require_teacher(request, session)
    else:
        user = {"role": "super_user", "id": None}

    submission = session.get(StudentSubmission, submission_id)
    if not submission:
        return RedirectResponse(url="/teacher", status_code=303)
    if not _can_view_submission(user, submission):
        return RedirectResponse(url="/teacher?error=not_assignee", status_code=303)
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
