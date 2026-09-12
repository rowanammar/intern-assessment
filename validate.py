#!/usr/bin/env python3

import urllib.request
import json
import subprocess
import sys
import time

BASE_URL = "http://localhost:8080"
TIMEOUT = 5
MAX_WAIT = 60


def check(url, method="GET", body=None):
    """
    Send an HTTP request and return (status_code, response_body_as_dict).
    If the request fails completely, return (0, None).
    """
    try:
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header("Content-Type", "application/json")
        else:
            req = urllib.request.Request(url, method=method)

        response = urllib.request.urlopen(req, timeout=TIMEOUT)
        text = response.read().decode("utf-8")
        try:
            data = json.loads(text)
        except:
            data = {"raw": text}
        return response.status, data

    except urllib.error.HTTPError as e:
        # Server responded, but with an error status (like 503)
        return e.code, None

    except Exception as e:
        # Could not connect at all
        print(f"    Connection error: {e}")
        return 0, None


def run_command(command):
    """
    Run a shell command and return its output as a string.
    """
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


def print_result(test_name, passed):
    """
    Print PASS or FAIL for a test, and return True/False.
    """
    if passed:
        print(f"  PASS  {test_name}")
    else:
        print(f"  FAIL  {test_name}")
    return passed


# === WAIT FOR SERVICES TO BE READY ===

def wait_for_ready():
    """
    Wait until NGINX is responding before running tests.
    This uses a bounded wait (won't wait forever).
    """
    print(f"Waiting for services (max {MAX_WAIT}s)...")
    start = time.time()

    while time.time() - start < MAX_WAIT:
        status, data = check(f"{BASE_URL}/health")
        if status == 200:
            print("  Services are up!\n")
            return True
        time.sleep(2)

    print("  FAIL  Services did not start in time.\n")
    return False


# === TEST FUNCTIONS ===

def test_public_access():
    """
    Test 1: Can we reach the system through NGINX on port 8080?
    """
    print("--- Test 1: Public Access ---")
    status, data = check(f"{BASE_URL}/")
    return print_result(
        f"GET / returns 200 (got {status})",
        status == 200
    )


def test_health_endpoint():
    """
    Test 2: Does /health work? (no dependency check, just app alive)
    """
    print("--- Test 2: Health Endpoint ---")
    status, data = check(f"{BASE_URL}/health")
    return print_result(
        f"GET /health returns 200 (got {status})",
        status == 200
    )


def test_ready_endpoint():
    """
    Test 3: Does /ready work? (checks PostgreSQL AND Redis)
    """
    print("--- Test 3: Readiness Endpoint ---")
    status, data = check(f"{BASE_URL}/ready")
    return print_result(
        f"GET /ready returns 200 (got {status})",
        status == 200
    )


def test_both_backends():
    """
    Test 4: Are BOTH app-01 and app-02 serving traffic?
    We hit /instance many times and collect the instance_ids.
    If we see both "app-01" and "app-02", both backends are working.
    """
    print("--- Test 4: Both Backends Respond ---")
    seen = set()

    for i in range(20):
        status, data = check(f"{BASE_URL}/instance")
        if status == 200 and data:
            instance = data.get("instance_id", "")
            seen.add(instance)

    got_both = "app-01" in seen and "app-02" in seen
    return print_result(
        f"Both backends respond via /instance (seen: {seen})",
        got_both
    )


def test_postgres():
    """
    Test 5: Can the app talk to PostgreSQL?
    We create a record with POST /records, then read it back with GET /records.
    """
    print("--- Test 5: PostgreSQL Connection ---")
    all_passed = True

    # Create a record
    status, data = check(
        f"{BASE_URL}/records",
        method="POST",
        body={"title": "validation test"}
    )
    all_passed = print_result(
        f"POST /records returns 201 (got {status})",
        status == 201
    ) and all_passed

    # Read records back
    status, data = check(f"{BASE_URL}/records")
    has_records = False
    if status == 200 and data:
        records = data.get("records", [])
        has_records = len(records) > 0

    all_passed = print_result(
        f"GET /records returns 200 with data (got {status}, has_records={has_records})",
        status == 200 and has_records
    ) and all_passed

    return all_passed


def test_redis():
    """
    Test 6: Can the app talk to Redis?
    We hit /counter twice. The number should go up.
    """
    print("--- Test 6: Redis Connection ---")

    status1, data1 = check(f"{BASE_URL}/counter")
    status2, data2 = check(f"{BASE_URL}/counter")

    counter_works = False
    if status1 == 200 and status2 == 200 and data1 and data2:
        val1 = data1.get("counter", 0)
        val2 = data2.get("counter", 0)
        counter_works = val2 > val1

    return print_result(
        f"GET /counter increments (got {status1} then {status2}, increasing={counter_works})",
        counter_works
    )


def test_unknown_route():
    """
    Test 7: Does an unknown route return 404?
    """
    print("--- Test 7: Unknown Route Returns 404 ---")
    status, data = check(f"{BASE_URL}/this-does-not-exist")
    return print_result(
        f"GET /this-does-not-exist returns 404 (got {status})",
        status == 404
    )


def test_network_isolation():
    """
    Test 8: NGINX should NOT be able to reach PostgreSQL or Redis directly.
    We use 'docker exec' to try connecting from inside the NGINX container.
    If the connection is refused or times out, isolation is working.
    """
    print("--- Test 8: Network Isolation ---")
    all_passed = True

    # Test: NGINX cannot reach PostgreSQL (port 5432)
    result = run_command(
        'docker exec nginx sh -c "wget -qO- --timeout=2 http://postgres:5432/ 2>&1 || echo BLOCKED"'
    )
    pg_blocked = "BLOCKED" in result or "timed out" in result or "bad address" in result.lower()
    all_passed = print_result(
        "NGINX cannot reach PostgreSQL",
        pg_blocked
    ) and all_passed

    # Test: NGINX cannot reach Redis (port 6379)
    result = run_command(
        'docker exec nginx sh -c "wget -qO- --timeout=2 http://redis:6379/ 2>&1 || echo BLOCKED"'
    )
    redis_blocked = "BLOCKED" in result or "timed out" in result or "bad address" in result.lower()
    all_passed = print_result(
        "NGINX cannot reach Redis",
        redis_blocked
    ) and all_passed

    return all_passed


def test_no_extra_host_ports():
    """
    Test 9: Only NGINX (port 8080) should be published to the host.
    PostgreSQL, Redis, and the apps should NOT have ports published.
    We check 'docker port' to see what ports are exposed.
    """
    print("--- Test 9: No Prohibited Host Ports ---")
    all_passed = True

    # Check each container that should NOT have host ports
    for name in ["postgres", "redis", "app-01", "app-02"]:
        output = run_command(f"docker port {name} 2>&1")
        # If 'docker port' returns nothing, no ports are published (good!)
        # If it returns an error, the container has no port mappings (also good!)
        has_host_port = output != "" and "Error" not in output
        all_passed = print_result(
            f"{name} has no published host ports",
            not has_host_port
        ) and all_passed

    return all_passed


# === MAIN: RUN ALL TESTS ===

def main():
    print("=" * 50)
    print("  BARQ ASSESSMENT - SYSTEM VALIDATION")
    print("=" * 50)
    print()

    # Wait for services first
    if not wait_for_ready():
        print("\nRESULT: FAIL (services not ready)")
        sys.exit(1)

    # Run every test and track results
    results = []
    results.append(test_public_access())
    results.append(test_health_endpoint())
    results.append(test_ready_endpoint())
    results.append(test_both_backends())
    results.append(test_postgres())
    results.append(test_redis())
    results.append(test_unknown_route())
    results.append(test_network_isolation())
    results.append(test_no_extra_host_ports())

    # Count results
    passed = sum(results)
    total = len(results)

    # Print summary
    print()
    print("=" * 50)
    if all(results):
        print(f"  RESULT: PASS ({passed}/{total} tests passed)")
        print("=" * 50)
        sys.exit(0)
    else:
        print(f"  RESULT: FAIL ({passed}/{total} tests passed)")
        print("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    main()
