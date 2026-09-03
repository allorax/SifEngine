from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    source_dataset = Column(String, index=True)
    source_record_id = Column(String)
    timestamp = Column(String, index=True, nullable=True)
    description = Column(Text, nullable=False)
    employer = Column(String, nullable=True)
    location = Column(String, nullable=True)
    state = Column(String, index=True, nullable=True)
    industry = Column(String, index=True, nullable=True)
    event = Column(String, nullable=True)
    source = Column(String, nullable=True)
    severity_info = Column(Text, nullable=True)
    extracted_info = Column(Text, nullable=True)
    raw_data = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)
    embedding_model = Column(String, index=True, nullable=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)

    cluster = relationship("Cluster", back_populates="reports")


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    cluster_num = Column(Integer, index=True)
    label = Column(String, nullable=False)
    report_count = Column(Integer, default=0)
    percentage = Column(Float, default=0.0)
    dominant_event = Column(String, nullable=True)
    dominant_hazard = Column(String, nullable=True)
    dominant_industry = Column(String, nullable=True)
    dominant_state = Column(String, nullable=True)
    min_date = Column(String, nullable=True)
    max_date = Column(String, nullable=True)

    reports = relationship("Report", back_populates="cluster")
    risk_score = relationship("RiskScore", uselist=False, back_populates="cluster")
    forecast = relationship("Forecast", uselist=False, back_populates="cluster")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), unique=True)
    risk_score = Column(Float, nullable=False)
    frequency = Column(Float, nullable=False)
    near_miss_intensity = Column(Float, nullable=False)
    severity = Column(Float, nullable=False)
    trend = Column(Float, nullable=False)
    recency = Column(Float, nullable=False)

    cluster = relationship("Cluster", back_populates="risk_score")


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), unique=True)
    trend_classification = Column(String, nullable=False)
    forecast_json = Column(Text, nullable=False)

    cluster = relationship("Cluster", back_populates="forecast")
