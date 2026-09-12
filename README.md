# BARQ DevOps Assessment

This repository contains the completed DevOps internship assessment, including the Flask API, PostgreSQL, Redis, and NGINX setup. 

All infrastructure is containerized using Docker and Docker Compose. Below you will find copyable commands to run the entire lifecycle of the project.

## Requirements
- Linux or WSL2
- Python 3.12
- Git
- Docker & Docker Compose

## 1. Setup & Build

Clone the repository and set up your local environment variables:

```bash
# Clone the repository
git clone <your-repo-url>
cd barq-academy

# Create the environment file
cp .env.example .env

# Set up the Python virtual environment for the test scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Start

Build the images and start the environment in detached mode:

```bash
docker compose -p barq-assessment up --build -d
```

Check the status to ensure `nginx`, `app-01`, `app-02`, `postgres`, and `redis` are running and healthy:

```bash
docker compose -p barq-assessment ps
```

## 3. Test (Validation)

Run the validation script to verify that all endpoints (`/`, `/health`, `/ready`, `/instance`, `/records`, `/counter`), databases, and network isolation are working correctly.

```bash
source .venv/bin/activate
python validate.py
```

## 4. Failure Test

Test the resilience of the environment by simulating a node failure. This script stops one backend instance, verifies NGINX failover, and then recovers the node.

```bash
source .venv/bin/activate
python failure_test.py
```

## 5. Backup & Restore

To take a snapshot of the PostgreSQL database:

```bash
./backup.sh
```
*(This will generate a backup file in the `backups/` directory)*

To restore the database from the latest backup (it safely restores to a temporary database first to verify integrity):

```bash
./restore.sh
```

### Persistence Verification
To verify data survives container recreation:
```bash
# 1. Create a test record
curl -X POST http://127.0.0.1:8080/records -H "Content-Type: application/json" -d '{"data": "persistence_test"}'

# 2. Destroy containers (but keep volumes)
docker compose -p barq-assessment down

# 3. Bring them back up
docker compose -p barq-assessment up -d

# 4. Check that the record is still there
curl http://127.0.0.1:8080/records
```

## 6. Cleanup (Stop)

To safely stop the lab without destroying persistent volumes:

```bash
docker compose -p barq-assessment down
```

To completely destroy the lab including the PostgreSQL and Redis data volumes (Warning: data will be lost):

```bash
docker compose -p barq-assessment down -v
```

---

## Documentation & Reports

Detailed answers to the assessment questions can be found in the accompanying reports:
- [Troubleshooting Journal](troubleshooting.md): Investigation logs, failed attempts, and root causes.
- [Log Analysis](log_analysis.md): Patterns, script outputs, and evidence.
- [Technical Decisions](decisions.md): Architecture choices, ports, timeouts, retries, and trade-offs.
- [Security Review](security_review.md): Identified risks, single points of failure, and production improvements.
- [AI Usage](AI_USAGE.md): How AI was used and verified during the task.
- [Architecture Diagram](architecture.png): Visual mapping of request flows, networks, and storage.
