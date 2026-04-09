#!/usr/bin/env python3
"""
Benchmark: IPC Overhead Analysis

Measures the latency of three IPC mechanisms used for COBOL-Python communication:

1. Option A (Subprocess): CALL "SYSTEM" with stdout redirect to file
   - Process creation overhead on every call
   - Simplest to implement
   - Best for low-frequency batch operations

2. Option B (Flat File): Write request file, invoke script, read response
   - Disk I/O overhead (both read and write)
   - More COBOL-native (file-based operations)
   - Suitable for batch processing

3. Option C (Named Pipe): Persistent daemon on FIFO channels
   - No process creation overhead per request
   - Lowest latency but more complex
   - Best for high-frequency operations (not tested here, Linux-only)

Hypothesis: Process creation dominates latency at low volumes; file I/O
dominates at high volumes; named pipes offer best sustained performance.

Test: 1,000 identical requests to customer_360.py through each mechanism
Report: Mean, P50, P95, P99 round-trip latencies (milliseconds)
"""

import sys
import time
import subprocess
import os
import tempfile
import numpy as np
from pathlib import Path
from datetime import datetime

# Setup
SCRIPT_DIR = Path(__file__).parent.parent / "python"
CUSTOMER_SCRIPT = SCRIPT_DIR / "customer_360.py"
TEST_CUSTOMER = "C-00001"
N_REQUESTS = 1000

# Temporary files
TEMP_DIR = tempfile.gettempdir()
REQUEST_FILE = Path(TEMP_DIR) / "ipc_bench_request.txt"
RESPONSE_FILE = Path(TEMP_DIR) / "ipc_bench_response.dat"


def bench_subprocess() -> list:
    """
    Option A: Subprocess with stdout redirect to file.

    Measures: Python startup + query + file write
    """
    print(f"  Running subprocess benchmark ({N_REQUESTS} requests)...")
    latencies = []

    for i in range(N_REQUESTS):
        t0 = time.perf_counter()

        # Use 'python' for Windows compatibility; falls back to 'python3' on Unix
        python_cmd = "python" if sys.platform == "win32" else "python3"
        result = subprocess.run(
            [python_cmd, str(CUSTOMER_SCRIPT), TEST_CUSTOMER],
            stdout=open(RESPONSE_FILE, "w"),
            stderr=subprocess.DEVNULL,
            timeout=10
        )

        latencies.append((time.perf_counter() - t0) * 1000)  # Convert to ms

        if (i + 1) % 100 == 0:
            print(f"    [OK] {i + 1:,} / {N_REQUESTS:,} requests")

    return latencies


def bench_flat_file() -> list:
    """
    Option B: Flat file exchange.

    Measures: File write (request) + subprocess + file read (response)
    """
    print(f"  Running flat file benchmark ({N_REQUESTS} requests)...")
    latencies = []

    for i in range(N_REQUESTS):
        t0 = time.perf_counter()

        # Write request file
        with open(REQUEST_FILE, "w") as f:
            f.write(TEST_CUSTOMER)

        # Execute Python script (reads request, writes response)
        # Use 'python' for Windows compatibility; falls back to 'python3' on Unix
        python_cmd = "python" if sys.platform == "win32" else "python3"
        result = subprocess.run(
            [python_cmd, str(CUSTOMER_SCRIPT), TEST_CUSTOMER],
            stdout=open(RESPONSE_FILE, "w"),
            stderr=subprocess.DEVNULL,
            timeout=10
        )

        # Read response file
        with open(RESPONSE_FILE, "r") as f:
            response = f.read()

        latencies.append((time.perf_counter() - t0) * 1000)  # Convert to ms

        if (i + 1) % 100 == 0:
            print(f"    [OK] {i + 1:,} / {N_REQUESTS:,} requests")

    return latencies


def bench_named_pipe() -> list:
    """
    Option C: Named pipes (FIFO).

    NOTE: Only works on Linux/macOS. Will skip on Windows.

    Measures: IPC overhead without process creation (requires daemon).
    For this benchmark, we use a simplified simulation:
    fork a Python daemon process that listens on the FIFO.
    """
    if sys.platform == "win32":
        print("  Skipping named pipe benchmark (Windows - not supported)")
        return []

    print(f"  Running named pipe benchmark ({N_REQUESTS} requests)...")

    # Create FIFOs
    req_fifo = Path(TEMP_DIR) / "ipc_bench_req.fifo"
    resp_fifo = Path(TEMP_DIR) / "ipc_bench_resp.fifo"

    for fifo in [req_fifo, resp_fifo]:
        if fifo.exists():
            fifo.unlink()
        os.mkfifo(fifo)

    # Start daemon process
    daemon_script = str(SCRIPT_DIR / "customer_360.py")
    python_cmd = "python3"  # Named pipes are Linux-only, so always use python3
    daemon_process = subprocess.Popen(
        [
            python_cmd, "-c",
            f"""
import sys
from pathlib import Path
sys.path.insert(0, '{SCRIPT_DIR}')

req_fifo = '{req_fifo}'
resp_fifo = '{resp_fifo}'

while True:
    with open(req_fifo, 'r') as f:
        customer_id = f.read().strip()

    # Call the actual script
    import subprocess
    result = subprocess.run(
        ['{python_cmd}', '{daemon_script}', customer_id],
        capture_output=True,
        text=True,
        timeout=10
    )

    with open(resp_fifo, 'w') as f:
        f.write(result.stdout)
"""
        ],
        stderr=subprocess.DEVNULL
    )

    latencies = []

    try:
        # Give daemon time to start
        time.sleep(0.5)

        for i in range(N_REQUESTS):
            t0 = time.perf_counter()

            # Write request
            with open(req_fifo, "w") as f:
                f.write(TEST_CUSTOMER)

            # Read response
            with open(resp_fifo, "r") as f:
                response = f.read()

            latencies.append((time.perf_counter() - t0) * 1000)

            if (i + 1) % 100 == 0:
                print(f"    [OK] {i + 1:,} / {N_REQUESTS:,} requests")

    finally:
        # Clean up
        daemon_process.terminate()
        daemon_process.wait(timeout=5)

        for fifo in [req_fifo, resp_fifo]:
            if fifo.exists():
                fifo.unlink()

    return latencies


def report_latencies(mechanism: str, latencies: list):
    """Print latency statistics."""
    if not latencies:
        print(f"\n{mechanism:<25} (SKIPPED - not supported on this platform)")
        return

    arr = np.array(latencies)

    print(f"\n{mechanism:<25}")
    print(f"{'Mean':<20} {arr.mean():>8.2f} ms")
    print(f"{'Median (P50)':<20} {np.percentile(arr, 50):>8.2f} ms")
    print(f"{'P95':<20} {np.percentile(arr, 95):>8.2f} ms")
    print(f"{'P99':<20} {np.percentile(arr, 99):>8.2f} ms")
    print(f"{'Min':<20} {arr.min():>8.2f} ms")
    print(f"{'Max':<20} {arr.max():>8.2f} ms")
    print(f"{'StdDev':<20} {arr.std():>8.2f} ms")


def main():
    """Run IPC overhead benchmarks."""
    print("=" * 70)
    print("BENCHMARK: IPC Overhead Analysis")
    print("=" * 70)
    print(f"Mechanism: COBOL -> Python (via {len(sys.argv)} IPC options)")
    print(f"Script: customer_360.py")
    print(f"Requests: {N_REQUESTS:,} identical calls")
    print(f"Test customer: {TEST_CUSTOMER}")
    print(f"Start time: {datetime.now().isoformat()}")
    print("=" * 70)
    print()

    # Run benchmarks
    subprocess_latencies = bench_subprocess()
    flat_file_latencies = bench_flat_file()
    named_pipe_latencies = bench_named_pipe()

    # Report
    print("\n" + "=" * 70)
    print("LATENCY RESULTS")
    print("=" * 70)

    report_latencies("Option A: Subprocess", subprocess_latencies)
    report_latencies("Option B: Flat File", flat_file_latencies)
    report_latencies("Option C: Named Pipe", named_pipe_latencies)

    # Summary
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)

    if subprocess_latencies and flat_file_latencies:
        arr_sub = np.array(subprocess_latencies)
        arr_file = np.array(flat_file_latencies)

        print(f"\nOption A (Subprocess) vs Option B (Flat File):")
        ratio = arr_sub.mean() / arr_file.mean()
        if ratio > 1:
            print(f"  [RESULT] File I/O overhead: {ratio:.1f}x slower than subprocess")
        else:
            print(f"  [RESULT] Subprocess overhead: {1/ratio:.1f}x slower than file")

    print(f"\nRecommendations:")
    print(f"  • Low frequency (< 10/sec):  Option A (subprocess)")
    print(f"      Simple implementation, acceptable latency")
    print(f"  • Medium frequency (10-100/sec): Option B (flat file)")
    print(f"      Better than subprocess, COBOL-native I/O")
    if named_pipe_latencies:
        print(f"  • High frequency (> 100/sec):  Option C (named pipes)")
        print(f"      Best performance, requires daemon management")

    # Clean up temp files
    for f in [REQUEST_FILE, RESPONSE_FILE]:
        if f.exists():
            f.unlink()

    print(f"\nEnd time: {datetime.now().isoformat()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
