import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from config import Config
from db.client import DBClient
from engine.telemetry import TelemetryCollector
from engine.analyzer import QueryAnalyzer
from git_ops.mcp_client import MCPClient
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def run_dbre_cycle():
    logger.info("Starting OmniQuery DBRE cycle...")
    
    db_client = DBClient()
    try:
        telemetry = TelemetryCollector(db_client)
        
        slow_queries = telemetry.collect_slow_queries()
        seq_scans = telemetry.collect_seq_scans()
        
        logger.info(f"Collected {len(slow_queries)} slow queries and {len(seq_scans)} seq scans.")
        
        analyzer = QueryAnalyzer(db_client)
        suggestions = analyzer.analyze(slow_queries, seq_scans)
        
        if suggestions:
            logger.info(f"Generated {len(suggestions)} optimization suggestions.")
            mcp = MCPClient()
            mcp.create_migration_pr(suggestions)
        else:
            logger.info("No optimizations needed at this time.")
            
    except Exception as e:
        logger.error(f"Error during DBRE cycle: {e}")
    finally:
        db_client.close()

if __name__ == "__main__":
    logger.info("Initializing OmniQuery DBRE Agent...")
    
    scheduler = BlockingScheduler()
    # Run the cycle initially
    run_dbre_cycle()
    
    # Schedule the recurring job
    scheduler.add_job(run_dbre_cycle, 'interval', seconds=Config.POLL_INTERVAL_SECONDS)
    
    logger.info(f"Scheduler started. Polling every {Config.POLL_INTERVAL_SECONDS} seconds.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down DBRE Agent.")
