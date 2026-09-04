from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DB_PATH

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    pool_pre_ping=True,
    pool_recycle=3600
)

# Enable SQLite WAL mode and optimizations for non-blocking concurrent reads & writes
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configure SQLite for high-performance WAL mode and concurrent reading."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for obtaining database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """Create tables and apply indexes & cache migration."""
    Base.metadata.create_all(bind=engine)
    columns = {column["name"] for column in inspect(engine).get_columns("reports")}
    with engine.begin() as connection:
        if "embedding_model" not in columns:
            connection.execute(text("ALTER TABLE reports ADD COLUMN embedding_model VARCHAR"))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_reports_embedding_cache "
            "ON reports (embedding_model, description)"
        ))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_reports_cluster_id "
            "ON reports (cluster_id)"
        ))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_reports_state "
            "ON reports (state)"
        ))
