#!/usr/bin/env python3
"""
Eyes on Tigers (EoT) — Streamlit Cloud Automated Health Check & Keep-Alive Probe

Prevents Streamlit Community Cloud hibernation by periodically probing the application,
logging latency metrics, and verifying server responsiveness.
"""

import sys
import time
import json
import argparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DEFAULT_APP_URL = "https://eyes-on-tigers-7mtepkv8ruq3aaulgr7ves.streamlit.app"

def ping_endpoint(url: str, timeout: int = 15) -> dict:
    """Sends an HTTP GET request with realistic browser headers to reset Streamlit idle timers."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 EyesOnTigers-HealthCheck/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    
    req = Request(url, headers=headers)
    start_time = time.perf_counter()
    
    try:
        with urlopen(req, timeout=timeout) as response:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            status_code = response.getcode()
            body_sample = response.read(1024).decode("utf-8", errors="ignore")
            
            # Check for Streamlit hibernation indicator
            is_asleep = "asleep" in body_sample.lower() or "get this app back up" in body_sample.lower()
            
            return {
                "url": url,
                "status": "ONLINE" if not is_asleep else "ASLEEP",
                "http_code": status_code,
                "latency_ms": round(latency_ms, 2),
                "is_asleep": is_asleep,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
    except HTTPError as e:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        # Streamlit Auth redirects (302/303) or standard redirects indicate the server is active
        is_active = e.code in (200, 301, 302, 303, 307, 308)
        return {
            "url": url,
            "status": "ONLINE (AUTH_PROTECTED)" if is_active else "HTTP_ERROR",
            "http_code": e.code,
            "latency_ms": round(latency_ms, 2),
            "is_asleep": False,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "message": str(e)
        }
    except URLError as e:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "url": url,
            "status": "UNREACHABLE",
            "http_code": 0,
            "latency_ms": round(latency_ms, 2),
            "is_asleep": False,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "error": str(e.reason)
        }
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "url": url,
            "status": "EXCEPTION",
            "http_code": 0,
            "latency_ms": round(latency_ms, 2),
            "is_asleep": False,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "error": str(e)
        }


def run_health_check(base_url: str) -> bool:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Probing Eyes on Tigers deployment: {base_url}...")
    
    # 1. Probe root web URL
    root_result = ping_endpoint(base_url)
    print(f"-> Root URL:       {root_result['status']} (HTTP {root_result['http_code']}, Latency: {root_result['latency_ms']} ms)")
    
    # 2. Probe dedicated lightweight health route
    health_url = f"{base_url.rstrip('/')}/?health=check"
    health_result = ping_endpoint(health_url)
    print(f"-> Health Route:   {health_result['status']} (HTTP {health_result['http_code']}, Latency: {health_result['latency_ms']} ms)")
    
    is_alive = root_result["http_code"] in (200, 301, 302, 303, 307, 308) or health_result["http_code"] in (200, 301, 302, 303, 307, 308)
    
    report = {
        "service": "Eyes on Tigers",
        "target": base_url,
        "is_alive": is_alive,
        "root_probe": root_result,
        "health_route_probe": health_result,
        "keep_alive_successful": is_alive
    }
    
    print("\nHealth Check Summary:")
    print(json.dumps(report, indent=2))
    return is_alive


def main():
    parser = argparse.ArgumentParser(description="Eyes on Tigers Keep-Alive & Health Check Probe")
    parser.add_argument("--url", default=DEFAULT_APP_URL, help="Streamlit Application URL")
    parser.add_argument("--daemon", action="store_true", help="Run continuously as a background daemon probe")
    parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds for daemon mode (default: 3600s / 1 hr)")
    args = parser.parse_args()

    if args.daemon:
        print(f"Starting Keep-Alive Daemon for {args.url} (Interval: {args.interval}s)...")
        while True:
            run_health_check(args.url)
            print(f"Sleeping for {args.interval}s until next probe...")
            time.sleep(args.interval)
    else:
        success = run_health_check(args.url)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
