from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report import ReportListItemRead, ReportRead
from app.services.report_builder import generate_cluster_report, get_report, list_reports


router = APIRouter()


@router.get("", response_model=list[ReportListItemRead])
def list_reports_route(db: Session = Depends(get_db)) -> list[ReportListItemRead]:
    return list_reports(db)


@router.get("/{report_id}", response_model=ReportRead)
def get_report_route(report_id: int, db: Session = Depends(get_db)) -> ReportRead:
    try:
        return get_report(db, report_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/clusters/{cluster_id}/generate", response_model=ReportRead)
def generate_cluster_report_route(
    cluster_id: int,
    report_type: str = Query(default="niche_report"),
    db: Session = Depends(get_db),
) -> ReportRead:
    try:
        return generate_cluster_report(db, cluster_id, report_type=report_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{report_id}/download")
def download_report_artifact(
    report_id: int,
    format: str = Query(default="markdown"),
    db: Session = Depends(get_db),
) -> FileResponse:
    try:
        report = get_report(db, report_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    format_key = format.casefold()
    path_lookup = {
        "markdown": report.markdown_path,
        "md": report.markdown_path,
        "pdf": report.pdf_path,
        "csv": report.csv_path,
        "json": report.json_path,
    }
    media_type_lookup = {
        "markdown": "text/markdown; charset=utf-8",
        "md": "text/markdown; charset=utf-8",
        "pdf": "application/pdf",
        "csv": "text/csv; charset=utf-8",
        "json": "application/json",
    }

    artifact_path = path_lookup.get(format_key)
    if artifact_path is None:
        raise HTTPException(status_code=404, detail=f"No artifact stored for format '{format}'.")

    resolved_path = Path(artifact_path)
    if not resolved_path.exists() or not resolved_path.is_file():
        raise HTTPException(status_code=404, detail="Artifact file does not exist on disk.")

    return FileResponse(
        path=resolved_path,
        media_type=media_type_lookup[format_key],
        filename=resolved_path.name,
    )
