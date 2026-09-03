from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_dataset: str
    source_record_id: Optional[str] = None
    timestamp: Optional[str] = None
    description: str
    employer: Optional[str] = None
    location: Optional[str] = None
    state: Optional[str] = None
    industry: Optional[str] = None
    event: Optional[str] = None
    source: Optional[str] = None
    severity_info: Optional[Dict[str, Any]] = None
    extracted_info: Optional[Dict[str, Any]] = None
    cluster_id: Optional[int] = None

class SimilarReportItem(BaseModel):
    id: int
    similarity: float
    description: str
    employer: Optional[str] = None
    timestamp: Optional[str] = None
    severity_info: Optional[Dict[str, Any]] = None


class SimilarReportsResponse(BaseModel):
    report_id: int
    similar_reports: List[SimilarReportItem]


class RiskScoreResponse(BaseModel):
    cluster_id: int
    risk_score: float
    frequency: float
    near_miss_intensity: float
    severity: float
    trend: float
    recency: float


class ForecastMonthItem(BaseModel):
    month: str
    predicted_count: float


class ForecastResponse(BaseModel):
    cluster_id: int
    trend: str
    forecast: List[ForecastMonthItem]


class ClusterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cluster_num: int
    label: str
    report_count: int
    percentage: float
    dominant_event: Optional[str] = None
    dominant_hazard: Optional[str] = None
    dominant_industry: Optional[str] = None
    dominant_state: Optional[str] = None
    min_date: Optional[str] = None
    max_date: Optional[str] = None

class DashboardSummaryResponse(BaseModel):
    total_reports: int
    total_clusters: int
    top_risk_clusters: List[Dict[str, Any]]
    emerging_clusters: List[Dict[str, Any]]
    increasing_clusters: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
