from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    niche_cluster_id: int
    title: str
    report_type: str
    markdown_content: str | None
    markdown_path: str | None
    pdf_path: str | None
    csv_path: str | None
    json_path: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class ReportListItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    niche_cluster_id: int
    title: str
    report_type: str
    markdown_path: str | None
    pdf_path: str | None
    csv_path: str | None
    json_path: str | None
    status: str
    created_at: datetime
    updated_at: datetime
