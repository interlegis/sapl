#!/usr/bin/env python3
"""
Script to test rate limiting of an endpoint.
"""

import argparse
import time
import requests
from collections import defaultdict
from urllib.parse import urlparse


def test_rate_limiter(url, num_requests=50, delay=0.1, timeout=10):
    """Send multiple requests and analyze rate limiting behavior."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(
            "URL must include a protocol and host, e.g. http://localhost or https://example.com"
        )
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Unsupported URL scheme: %s. Use http or https." % parsed.scheme)

    status_counts = defaultdict(int)
    response_times = []
    first_rate_limited_at = None
    attempted_requests = 0
    
    print(f"Testing rate limiter on: {url}")
    print(f"Number of requests: {num_requests}")
    print(f"Delay between requests: {delay}s")
    print("-" * 50)
    
    for i in range(num_requests):
        attempted_requests += 1
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            elapsed = time.time() - start_time
            
            status_counts[response.status_code] += 1
            response_times.append(elapsed)
            
            print(f"Request {i+1:3d}: Status {response.status_code} | Time: {elapsed:.3f}s")
            
            if response.status_code == 429:
                if first_rate_limited_at is None:
                    first_rate_limited_at = i + 1
                print(f"  -> Rate limited on request {i+1}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Request {i+1:3d}: Error - {e}")
            status_counts['ERROR'] += 1
        
        if i < num_requests - 1:
            time.sleep(delay)
    
    print("-" * 50)
    print("\nSummary:")
    print(f"  Total requests attempted: {attempted_requests}")
    print(f"  Successful (200):          {status_counts.get(200, 0)}")
    print(f"  Rate limited (429):        {status_counts.get(429, 0)}")
    if first_rate_limited_at is not None:
        print(f"  First 429 occurred at request: {first_rate_limited_at}")
    print(f"  Other errors:              {sum(v for k, v in status_counts.items() if k not in [200, 429, 'ERROR'])}")
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        print(f"\nAverage response time: {avg_time:.3f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test rate limiter of a URL")
    parser.add_argument(
        "url",
        help="URL to test, including protocol (http:// or https://)",
    )
    parser.add_argument("-n", "--num-requests", type=int, default=50, help="Number of requests")
    parser.add_argument("-d", "--delay", type=float, default=0.1, help="Delay between requests (seconds)")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Request timeout (seconds)")
    
    args = parser.parse_args()
    test_rate_limiter(args.url, args.num_requests, args.delay, args.timeout)