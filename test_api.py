"""
test_api.py
───────────
Quick test script to verify all API endpoints work.
Run AFTER starting the API with: python api.py

Usage:
    python test_api.py
    python test_api.py --file path/to/your.pdf
"""

import argparse
import json
import time
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_KEY  = "dev-key-change-in-production"  # matches default in api.py
HEADERS  = {"X-API-Key": API_KEY}


def test_health():
    print("\n── Health check ──────────────────────────────")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print(f"  ✅ {r.json()}")


def test_auth_rejected():
    print("\n── Auth rejection ────────────────────────────")
    r = requests.get(f"{BASE_URL}/jobs", headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print(f"Invalid key correctly rejected (401)")


def test_upload_and_poll(file_path: str):
    print(f"\n── Upload: {Path(file_path).name} ──────────────────────")

    # Upload file
    with open(file_path, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/analyze",
            headers=HEADERS,
            files={"file": (Path(file_path).name, f, "application/pdf")},
            data={"contract_type": "auto"},
        )

    assert r.status_code == 200, f"Upload failed: {r.text}"
    job = r.json()
    job_id = job["job_id"]
    print(f"     Job created: {job_id}")
    print(f"     Status: {job['status']}")

    # Poll until complete or failed
    print(f"\n── Polling job {job_id[:8]}... ──────────────────")
    max_wait = 300  # 5 minutes
    interval = 5
    elapsed  = 0

    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval

        r = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=HEADERS)
        assert r.status_code == 200
        status_data = r.json()
        status = status_data["status"]
        print(f"  [{elapsed:3d}s] Status: {status}")

        if status == "complete":
            print(f"\n   Pipeline complete!")
            print(f"     Download URLs:")
            for key, url in status_data.get("download_urls", {}).items():
                print(f"       {key}: {BASE_URL}{url}")
            return job_id, status_data

        if status == "failed":
            print(f"\n   Pipeline failed: {status_data.get('error')}")
            return job_id, status_data

    print(f"\n  ⏱ Timed out after {max_wait}s")
    return job_id, {}


def test_download(job_id: str, doc_type: str):
    print(f"\n── Download {doc_type.upper()} ──────────────────────────────")
    r = requests.get(
        f"{BASE_URL}/download/{job_id}/{doc_type}",
        headers=HEADERS,
    )
    assert r.status_code == 200, f"Download failed: {r.status_code} {r.text}"
    assert r.headers["content-type"] == "application/pdf"

    out_path = f"test_download_{doc_type}.pdf"
    with open(out_path, "wb") as f:
        f.write(r.content)
    print(f"   Downloaded {len(r.content):,} bytes → {out_path}")


def test_list_jobs():
    print("\n── List jobs ─────────────────────────────────")
    r = requests.get(f"{BASE_URL}/jobs", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    print(f"   {data['total']} job(s) in system")


def test_delete_job(job_id: str):
    print(f"\n── Delete job {job_id[:8]} ──────────────────────────")
    r = requests.delete(f"{BASE_URL}/jobs/{job_id}", headers=HEADERS)
    assert r.status_code == 200
    print(f"   Job deleted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="tests/fixtures/deal-intake-sample-structured.pdf",
                        help="PDF file to test with")
    parser.add_argument("--skip-delete", action="store_true",
                        help="Keep job after test (don't delete)")
    args = parser.parse_args()

    print("=" * 50)
    print("  Contract Intelligence API — Test Suite")
    print("=" * 50)

    try:
        test_health()
        test_auth_rejected()

        if Path(args.file).exists():
            job_id, result = test_upload_and_poll(args.file)

            if result.get("status") == "complete":
                test_download(job_id, "nda")
                test_download(job_id, "sow")

            test_list_jobs()

            if not args.skip_delete:
                test_delete_job(job_id)
        else:
            print(f"\n⚠ Test file not found: {args.file}")
            print("  Run with --file path/to/your.pdf to test upload")
            test_list_jobs()

        print("\n" + "=" * 50)
        print("   All tests passed")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n Test failed: {e}")
    except requests.exceptions.ConnectionError:
        print("\n Cannot connect to API — is it running?")
        print("   Start it with: python api.py")
