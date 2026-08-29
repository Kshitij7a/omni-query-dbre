import logging
from db.client import DBClient

logger = logging.getLogger(__name__)

class TelemetryCollector:
    def __init__(self, db_client: DBClient):
        self.db = db_client

    def collect_slow_queries(self):
        query = """
            SELECT queryid, query, calls, total_exec_time, mean_exec_time, rows
            FROM pg_stat_statements
            WHERE calls >= 10 AND mean_exec_time >= 0.0
            ORDER BY total_exec_time DESC
            LIMIT 50;
        """
        logger.info("Collecting slow queries telemetry...")
        return self.db.fetch_all(query)

    def collect_seq_scans(self):
        query = """
            SELECT relname AS table_name, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch
            FROM pg_stat_user_tables
            WHERE seq_scan > 10 AND seq_tup_read > 10000
            ORDER BY seq_tup_read DESC
            LIMIT 50;
        """
        logger.info("Collecting sequential scan telemetry...")
        return self.db.fetch_all(query)
