# OmniQuery DBRE 🚀

An autonomous Database Reliability Engineering (DBRE) agent that proactively analyzes PostgreSQL telemetry, detects inefficiencies, and issues zero-downtime `.sql` migrations through GitHub Pull Requests.

## System Architecture

OmniQuery DBRE is built exclusively for backend mechanics, following strict event-driven loops:

### 1. The Telemetry Loop
- The core daemon (driven by `APScheduler` in `main.py`) continuously polls the database on a configurable interval (e.g., every 10 seconds for testing).
- It connects securely to PostgreSQL via read-only constraints (`engine/telemetry.py`) and gathers data directly from system catalogs (`pg_stat_statements`, `pg_stat_user_tables`).
- Anomalies such as missing indexes or highly unoptimized sequential scans are identified dynamically.

### 2. Execution RAG (Explain & Analyze)
- The system doesn't just guess optimizations. It retrieves the exact slow query, substitutes normalized parameters, and runs `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`.
- `engine/analyzer.py` deeply parses the resulting execution plan JSON tree to extract the `Total Cost`, `Actual Total Time`, and traverse for missing `Seq Scan` flags.
- By marrying raw query timing with the precise execution engine metrics, the agent establishes highly accurate context for its tuning recommendations.

### 3. Safe Deployments via MCP GitOps
- Safety is paramount. The DBRE agent never executes DDL (like `CREATE INDEX`) directly against the live database.
- Instead, optimizations are formulated as `.sql` scripts (using non-blocking `CONCURRENTLY` modifiers).
- Using PyGithub in `github/mcp_client.py` (or `git_ops/mcp_client.py`), it creates a new branch on the target repository, commits the generated migration file, and opens a Pull Request automatically.
- A human DBRE team member can review the RAG context and the PR, ensuring fully audited, zero-downtime database updates.

## Getting Started

1. Copy `.env.example` to `.env` and fill in your credentials.
2. Spin up the infrastructure via `docker-compose up -d`.
3. Install dependencies: `pip install -r requirements.txt`.
4. (Optional) Run `python scripts/seed_workload.py` to populate a messy, unindexed dataset to observe the agent in action.
5. Start the telemetry loop: `python main.py`.

## Constraints & Design Philosophies
- **Pure Backend Focus:** The system is purely data and API driven. No UI dashboards or HTML wrappers are present.
- **Safety First:** Read-only connections for telemetry, GitOps for schema changes.
