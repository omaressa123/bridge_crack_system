"""
Incremental schema migrations for existing MySQL databases.

create_all() only creates new tables; this module applies safe ALTER statements
for column additions, index creation, and data backfills on existing deployments.
"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def _index_exists(inspector, table_name: str, index_name: str) -> bool:
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def _add_column(conn, table: str, column: str, definition: str) -> None:
    conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}"))


def _create_index(conn, table: str, index_name: str, columns: str) -> None:
    conn.execute(text(f"CREATE INDEX `{index_name}` ON `{table}` ({columns})"))


def _backfill_nulls(conn, table: str, column: str, value: str) -> None:
    conn.execute(text(f"UPDATE `{table}` SET `{column}` = {value} WHERE `{column}` IS NULL"))


def run_migrations(engine: Engine) -> None:
    inspector = inspect(engine)

    with engine.begin() as conn:
        if _table_exists(inspector, "bridges"):
            if not _column_exists(inspector, "bridges", "created_at"):
                _add_column(conn, "bridges", "created_at", "DATETIME NULL")
                conn.execute(text("UPDATE `bridges` SET `created_at` = `inspection_date` WHERE `created_at` IS NULL"))
                conn.execute(text("UPDATE `bridges` SET `created_at` = UTC_TIMESTAMP() WHERE `created_at` IS NULL"))
            if not _column_exists(inspector, "bridges", "updated_at"):
                _add_column(conn, "bridges", "updated_at", "DATETIME NULL")
                conn.execute(text("UPDATE `bridges` SET `updated_at` = `created_at` WHERE `updated_at` IS NULL"))
            if not _column_exists(inspector, "bridges", "image_path"):
                _add_column(conn, "bridges", "image_path", "VARCHAR(500) NULL")
            if not _column_exists(inspector, "bridges", "inspection_schedule"):
                _add_column(conn, "bridges", "inspection_schedule", "VARCHAR(255) NULL")
            if not _column_exists(inspector, "bridges", "metadata_json"):
                _add_column(conn, "bridges", "metadata_json", "TEXT NULL")

        if _table_exists(inspector, "inspection_reports"):
            if not _column_exists(inspector, "inspection_reports", "created_at"):
                _add_column(conn, "inspection_reports", "created_at", "DATETIME NULL")
                conn.execute(
                    text("UPDATE `inspection_reports` SET `created_at` = `report_date` WHERE `created_at` IS NULL")
                )
            _backfill_nulls(conn, "inspection_reports", "total_cracks_detected", "0")
            _backfill_nulls(conn, "inspection_reports", "high_severity_cracks", "0")
            _backfill_nulls(conn, "inspection_reports", "status", "'Pending'")

        if _table_exists(inspector, "users"):
            if not _column_exists(inspector, "users", "updated_at"):
                _add_column(conn, "users", "updated_at", "DATETIME NULL")
                conn.execute(text("UPDATE `users` SET `updated_at` = `created_at` WHERE `updated_at` IS NULL"))

            # Normalize legacy integer is_active (0/1) to boolean semantics
            conn.execute(text("UPDATE `users` SET `is_active` = 1 WHERE `is_active` IS NULL"))

        if _table_exists(inspector, "crack_detections"):
            _backfill_nulls(conn, "crack_detections", "severity_level", "1")
            _backfill_nulls(conn, "crack_detections", "crack_type", "'unknown'")
            if not _column_exists(inspector, "crack_detections", "status"):
                _add_column(conn, "crack_detections", "status", "VARCHAR(30) NOT NULL DEFAULT 'pending'")
            if not _column_exists(inspector, "crack_detections", "notes"):
                _add_column(conn, "crack_detections", "notes", "TEXT NULL")
            if not _column_exists(inspector, "crack_detections", "reviewed_by"):
                _add_column(conn, "crack_detections", "reviewed_by", "INT NULL")
            if not _column_exists(inspector, "crack_detections", "reviewed_at"):
                _add_column(conn, "crack_detections", "reviewed_at", "DATETIME NULL")

        # Indexes (idempotent checks)
        index_specs = [
            ("crack_detections", "ix_crack_detections_bridge_id", "bridge_id"),
            ("crack_detections", "ix_crack_detections_detected_at", "detected_at"),
            ("crack_detections", "ix_crack_detections_crack_identifier", "crack_identifier"),
            ("crack_detections", "ix_crack_bridge_detected", "bridge_id, detected_at"),
            ("crack_detections", "ix_crack_bridge_identifier", "bridge_id, crack_identifier"),
            ("sensor_data", "ix_sensor_data_bridge_id", "bridge_id"),
            ("sensor_data", "ix_sensor_data_timestamp", "timestamp"),
            ("sensor_data", "ix_sensor_bridge_timestamp", "bridge_id, timestamp"),
            ("inspection_reports", "ix_inspection_reports_bridge_id", "bridge_id"),
            ("inspection_reports", "ix_inspection_reports_report_date", "report_date"),
            ("inspection_reports", "ix_inspection_reports_created_by", "created_by"),
        ]

        for table, index_name, columns in index_specs:
            if _table_exists(inspector, table) and not _index_exists(inspector, table, index_name):
                try:
                    _create_index(conn, table, index_name, columns)
                    logger.info("Created index %s on %s", index_name, table)
                except Exception:
                    logger.warning("Could not create index %s on %s", index_name, table, exc_info=True)

    logger.info("Database migrations complete")
