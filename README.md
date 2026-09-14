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

## Questions

### What failed first? What proved the cause? Which failed attempt taught you something?

The first thing that failed was NGINX not responding at all on port 8080. I ran `curl http://127.0.0.1:8080/` and got "Connection reset by peer". The cause was a port mismatch in docker-compose.yml — it was forwarding traffic to port 81 but NGINX was listening on port 80. After fixing that I got a 502 Bad Gateway instead, which was progress but still broken. I then fixed a typo in the healthcheck URL (`/healthz` instead of `/health`) and the apps became healthy, but 502 persisted. The failed attempt that taught me somthing was when I changed the port in nginx.conf thinking that was the problem, but it still did not work. That made me look deeper and I found that `APP_HOST` was set to `127.0.0.1` in docker-compose.yml, which made the Flask app only listen to itself inside the container. Changing it to `0.0.0.0` finally fixed everything. Full details are in [troubleshooting.md](troubleshooting.md), entries 1 through 3.

### What patterns did the logs reveal? How did you avoid double-counting requests?

The logs covered a 30-minute window from 11:00 to 11:30 UTC. There were four distinct failure periods — the first spike at 11:05 was caused by app-02 going down (502 errors with "Connection refused" in the error log), then at 11:12 Redis became unavailable causing 503 errors, then at 11:20 PostgreSQL had an "invalid password" error, and finally at 11:25 there were 504 Gateway Timeouts that were probably caused by a CPU spike or server slowdown. To avoid double-counting, I extracted all the request IDs using `grep` and `sort -u` to keep only unique entries, which gave me 720 distinct requests out of 725 valid lines. Full commands and output are in [log_analysis.md](log_analysis.md).

### How do requests flow? Why these ports, networks and readiness checks?

A client sends a request to `localhost:8080` which hits NGINX on port 80 inside the container. NGINX load balances between app-01 and app-02 on port 8080 using round-robin. The Flask apps talk to PostgreSQL on port 5432 and Redis on port 6379. Only NGINX is published on the host — the apps and databases have no published ports so they cannot be reached directly. I used two networks: frontend for NGINX and the apps, and backend (internal) for the apps and the databases. This way NGINX cannot talk to PostgreSQL or Redis directly. I used `/health` for the Docker healthcheck instead of `/ready` because `/health` only checks if Flask is alive. If I used `/ready`, the container would restart every time Redis was slow, which would make things worse. See [decisions.md](decisions.md), decision 2 for the full explanation and the [architecture diagram](architecture.png) for the visual layout.

### Why these timeouts, retries, restart settings and resource limits?

I set `proxy_connect_timeout` to 2 seconds and `proxy_read_timeout` to 3 seconds in nginx.conf because if a backend does not respond within that time, it is probably down and there is no point waiting longer. I enabled `proxy_next_upstream` on error, timeout, 502 and 503 so that when one backend crashes, NGINX automatically retries the request on the other backend instead of showing an error to the user. I set `max_fails=2` with `fail_timeout=10s` so NGINX marks a backend as down after 2 failures and stops trying it for 10 seconds. For resource limits, I gave the apps and databases 0.50 CPU and 128-256MB memory to prevent one container from eating all the RAM. I used `restart: unless-stopped` instead of `restart: always` so containers come back after a crash but stay stopped if I manually stop them. Full reasoning in [decisions.md](decisions.md), decisions 3 and 4.

### When should validation fail? What does green CI prove, or not prove?

Validation should fail when any of these happen: an endpoint returns the wrong status code, only one backend responds instead of both, PostgreSQL or Redis is unreachable, NGINX can directly reach PostgreSQL or Redis (network isolation broken), or any of the apps or databases have published host ports. The script exits with a non-zero code on failure so CI catches it. Green CI proves that the Docker images build correctly, the containers start and become healthy, all endpoints work, both backends serve traffic, network isolation is in place, and no extra ports are published. But green CI does not prove that the system handles real production load, that backups actually restore correctly, or that the system survives a real hardware failure. CI runs on a fresh environment every time so it also does not prove that data persists across restarts.

### Which single points of failure remain? How would you fix them in production?

The biggest single point of failure is PostgreSQL — there is only one instance, so if it goes down, the entire system loses database access and `/records` stops working. I would fix this in production by adding a read replica with automatic failover using something like Patroni. NGINX is also a single point of failure because all traffic goes through one container. In production I would put a cloud load balancer in front of it. Redis is another one — if it crashes, the counter stops working. In production I would use Redis Sentinel or a managed Redis cluster. The Docker host itself is a single point of failure too. In production I would run this on Kubernetes across multiple nodes in different availability zones. See [security_review.md](security_review.md), item 8 for more details.

### What would you improve? How did you verify AI-assisted work?

I would add Prometheus and Grafana for monitoring so I can see CPU and memory usage and get alerts before something crashes instead of finding out after. I would add TLS termination on NGINX so traffic is encrypted. I would use a secret manager like HashiCorp Vault instead of `.env` files. I would also add rate limiting in NGINX to protect against DDoS. For AI verification, I tested and verified everything myself. Every time the AI gave me code or commands, I ran them locally and checked the output before using them. For example, the first restore script the AI gave me was dangerous because it dropped the real database immediately, so I asked it to make a safer version that restores to a temp database first, and then I tested it by deleting volumes and restoring to make sure it actually works. Full AI disclosure is in [AI_USAGE.md](AI_USAGE.md).

---

## Documentation & Reports

- [Troubleshooting Journal](troubleshooting.md): Investigation logs, failed attempts, and root causes.
- [Log Analysis](log_analysis.md): Patterns, script outputs, and evidence.
- [Technical Decisions](decisions.md): Architecture choices, ports, timeouts, retries, and trade-offs.
- [Security Review](security_review.md): Identified risks, single points of failure, and production improvements.
- [AI Usage](AI_USAGE.md): How AI was used and verified during the task.
- [Architecture Diagram](architecture.png): Visual mapping of request flows, networks, and storage.
