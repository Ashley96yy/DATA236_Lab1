from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


PASSWORD = "Passw0rd!"


def signup_user(base_url: str, email: str, password: str) -> None:
    payload = json.dumps(
        {
            "name": email.split("@")[0],
            "email": email,
            "password": password,
        }
    ).encode("utf-8")

    request = Request(
        f"{base_url.rstrip('/')}/api/v1/auth/signup",
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request) as response:
            if response.status not in (200, 201):
                raise RuntimeError(f"Unexpected signup status for {email}: {response.status}")
    except HTTPError as error:
        if error.code != 409:
            raise


def prepare_users(base_url: str, count: int, prefix: str, output_path: Path, restaurant_id: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for index in range(1, count + 1):
        email = f"{prefix}{index:03d}@example.com"
        signup_user(base_url, email, PASSWORD)
        rows.append([email, PASSWORD, restaurant_id, 5, f"JMeter performance review {prefix}-{index:03d}"])

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["email", "password", "restaurant_id", "rating", "comment"])
        writer.writerows(rows)

    print(f"Prepared {count} load-test users.")
    print(f"CSV: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare JMeter users via the signup API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Gateway base URL")
    parser.add_argument("--count", type=int, required=True, help="Number of users to generate")
    parser.add_argument("--prefix", required=True, help="Unique email prefix, e.g. review100_")
    parser.add_argument("--output", required=True, help="CSV output path")
    parser.add_argument("--restaurant-id", type=int, default=1, help="Restaurant ID for create-review tests")
    args = parser.parse_args()

    prepare_users(
        base_url=args.base_url,
        count=args.count,
        prefix=args.prefix,
        output_path=Path(args.output).resolve(),
        restaurant_id=args.restaurant_id,
    )


if __name__ == "__main__":
    main()
