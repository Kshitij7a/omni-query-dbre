import logging
import re
import json
from db.client import DBClient

logger = logging.getLogger(__name__)

class QueryAnalyzer:
    def __init__(self, db_client: DBClient):
        self.db = db_client

    def extract_metrics_from_plan(self, plan_node):
        metrics = {
            'total_cost': plan_node.get('Total Cost'),
            'actual_total_time': plan_node.get('Actual Total Time'),
            'shared_hit_blocks': plan_node.get('Shared Hit Blocks'),
            'has_seq_scan': False,
            'seq_scan_table': None
        }
        
        def traverse(node):
            if node.get('Node Type') == 'Seq Scan':
                metrics['has_seq_scan'] = True
                metrics['seq_scan_table'] = node.get('Relation Name')
            if 'Plans' in node:
                for child in node['Plans']:
                    traverse(child)
                    
        traverse(plan_node)
        return metrics

    def analyze(self, slow_queries, seq_scans):
        """
        Analyzes telemetry using EXPLAIN and suggests migrations.
        """
        suggestions = []
        
        for q in slow_queries:
            query_text = q['query']
            
            # Simple substitution for parameterized queries to allow EXPLAIN to run
            executable_query = re.sub(r'\$[0-9]+', "'1'", query_text)
            
            explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {executable_query}"
            
            try:
                results = self.db.fetch_all(explain_sql)
                if results and len(results) > 0:
                    # Depending on psycopg2 version, QUERY PLAN could be a list of dicts or string
                    plan_data = results[0].get('QUERY PLAN', [])
                    if isinstance(plan_data, str):
                        plan_data = json.loads(plan_data)
                    
                    if plan_data and isinstance(plan_data, list):
                        plan_node = plan_data[0].get('Plan', {})
                        metrics = self.extract_metrics_from_plan(plan_node)
                        
                        logger.info(f"Query Metrics for '{query_text[:50]}...': {metrics}")
                        
                        if metrics['has_seq_scan'] and metrics['seq_scan_table']:
                            table_name = metrics['seq_scan_table']
                            
                            # Fallback regex to find column for the index
                            match = re.search(r"where\s+([a-z0-9_]+)\s*=", query_text.lower())
                            if match:
                                column_name = match.group(1)
                                idx_name = f"idx_{table_name}_{column_name}"
                                suggestion = f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {idx_name} ON {table_name} ({column_name});"
                                
                                if suggestion not in suggestions:
                                    suggestions.append(suggestion)
                                    logger.info(f"Suggested index based on EXPLAIN: {suggestion}")
            except Exception as e:
                logger.error(f"Failed to EXPLAIN query: {query_text}. Error: {e}")
                
        return suggestions
