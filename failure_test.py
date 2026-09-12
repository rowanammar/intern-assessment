#!/usr/bin/env python3

import urllib.request
import json
import subprocess
import sys
import time

BASE_URL = "http://localhost:8080"
TIMEOUT = 5
BACKEND_TO_KILL = "app-02"
SURVIVING_BACKEND = "app-01"



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
        return e.code, None

    except Exception:
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


def send_traffic(num_requests):
    """
    Send a bunch of requests and count successes, errors,
    and which backends responded.
    Returns a dictionary with the results.
    """
    successes = 0
    errors = 0
    backends_seen = set()

    for i in range(num_requests):
        status, data = check(f"{BASE_URL}/instance")
        if status == 200 and data:
            successes += 1
            instance = data.get("instance_id", "unknown")
            backends_seen.add(instance)
        else:
            errors += 1

    return {
        "successes": successes,
        "errors": errors,
        "total": num_requests,
        "backends_seen": backends_seen,
    }


def wait_for_backend(backend_name, max_wait=60):
    """
    Wait until a specific backend starts responding through NGINX.
    """
    start = time.time()
    while time.time() - start < max_wait:
        status, data = check(f"{BASE_URL}/instance")
        if status == 200 and data:
            if data.get("instance_id") == backend_name:
                return True
        time.sleep(1)
    return False


def main():
    all_passed = True

    print("--- Step 1: Verify system is healthy before test ---")

    status, data = check(f"{BASE_URL}/health")
    all_passed = print_result(
        f"System is healthy (got {status})",
        status == 200
    ) and all_passed

    if not all_passed:
        print("\nSystem is not healthy. Cannot run failure test.")
        print("Start your containers first: docker compose up -d")
        sys.exit(1)

    # Confirm both backends are responding
    traffic = send_traffic(20)
    both_up = BACKEND_TO_KILL in traffic["backends_seen"] and SURVIVING_BACKEND in traffic["backends_seen"]
    all_passed = print_result(
        f"Both backends responding before test (seen: {traffic['backends_seen']})",
        both_up
    ) and all_passed

    if not both_up:
        print("\nBoth backends need to be running before the test starts.")
        sys.exit(1)

    print()

    print(f"--- Step 2: Stopping {BACKEND_TO_KILL} ---")

    run_command(f"docker stop {BACKEND_TO_KILL}")
    time.sleep(2)

    # Verify it actually stopped
    container_status = run_command(f"docker inspect -f '{{{{.State.Running}}}}' {BACKEND_TO_KILL}")
    is_stopped = "false" in container_status.lower()
    all_passed = print_result(
        f"{BACKEND_TO_KILL} is stopped",
        is_stopped
    ) and all_passed

    print()

    print(f"--- Step 3: Sending traffic with {BACKEND_TO_KILL} down ---")

    traffic_during_failure = send_traffic(20)

    print(f"    Requests sent: {traffic_during_failure['total']}")
    print(f"    Successes:     {traffic_during_failure['successes']}")
    print(f"    Errors:        {traffic_during_failure['errors']}")
    print(f"    Backends seen: {traffic_during_failure['backends_seen']}")

    # The surviving backend should be handling all traffic
    all_passed = print_result(
        f"Traffic still served by {SURVIVING_BACKEND}",
        SURVIVING_BACKEND in traffic_during_failure["backends_seen"]
    ) and all_passed

    # The stopped backend should NOT appear
    all_passed = print_result(
        f"{BACKEND_TO_KILL} is NOT serving traffic",
        BACKEND_TO_KILL not in traffic_during_failure["backends_seen"]
    ) and all_passed

    # At least some requests should succeed (system stays available)
    all_passed = print_result(
        f"System stayed available ({traffic_during_failure['successes']}/{traffic_during_failure['total']} succeeded)",
        traffic_during_failure["successes"] > 0
    ) and all_passed

    print()

    print(f"--- Step 4: Restarting {BACKEND_TO_KILL} ---")

    run_command(f"docker start {BACKEND_TO_KILL}")

    # Wait for it to come back and be healthy
    print(f"    Waiting for {BACKEND_TO_KILL} to become healthy...")
    came_back = wait_for_backend(BACKEND_TO_KILL, max_wait=60)

    all_passed = print_result(
        f"{BACKEND_TO_KILL} is back and serving traffic",
        came_back
    ) and all_passed

    print()

    print("--- Step 5: Verify full recovery ---")

    # Give it a moment to stabilize
    time.sleep(3)

    traffic_after_recovery = send_traffic(20)

    print(f"    Requests sent: {traffic_after_recovery['total']}")
    print(f"    Successes:     {traffic_after_recovery['successes']}")
    print(f"    Errors:        {traffic_after_recovery['errors']}")
    print(f"    Backends seen: {traffic_after_recovery['backends_seen']}")

    # Both backends should be responding again
    both_back = BACKEND_TO_KILL in traffic_after_recovery["backends_seen"] and SURVIVING_BACKEND in traffic_after_recovery["backends_seen"]
    all_passed = print_result(
        f"Both backends responding after recovery (seen: {traffic_after_recovery['backends_seen']})",
        both_back
    ) and all_passed

    # No errors after recovery
    all_passed = print_result(
        f"No errors after recovery ({traffic_after_recovery['errors']} errors)",
        traffic_after_recovery["errors"] == 0
    ) and all_passed
    print()
    print("=" * 50)
    if all_passed:
        print("  RESULT: PASS - System survived failure and recovered")
        print("=" * 50)
        sys.exit(0)
    else:
        print("  RESULT: FAIL - Something went wrong during the test")
        print("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    main()
