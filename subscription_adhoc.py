import requests
from requests_oauthlib import OAuth1
import os
import sys
import argparse

# --- Configuration ---
# It's recommended to use environment variables for secrets in production
CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("TWITTER_CONSUMER_SECRET")
ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
WEBHOOK_ID = os.environ.get("TWITTER_WEBHOOK_ID")

if not all([CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, WEBHOOK_ID]):
    print("Error: Missing one or more environment variables. ", file=sys.stderr)
    print("Please set TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, and TWITTER_WEBHOOK_ID environment variables.", file=sys.stderr)
    sys.exit(1)

API_BASE_URL = "https://api.x.com/2"

# Dtab overrides for staging environment (adjust if needed)
STAGING1_DTAB_OVERRIDES = [
    "/s/data-webhooks/webhooks-config-api => /srv#/staging1/atla/data-webhooks/webhooks-config-api:thrift",
    "/s/data-webhooks/webhooks-server:thrift => /srv#/staging1/atla/data-webhooks/webhooks-server:thrift",
    "/s/data-accountactivity/accountactivity-subscriptions-api:thrift => /srv#/staging1/atla/data-accountactivity/accountactivity-subscriptions-api:thrift",
    "/s/data-accountactivity/aaaconfigsvc:https => /srv#/staging1/atla/data-accountactivity/aaaconfigsvc:https",
    "/s/data-accountactivity/accountactivity-replay-api:thrift => /srv#/staging1/atla/data-accountactivity/accountactivity-replay-api:thrift",
]

def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Check Twitter webhook subscription status.")
    parser.add_argument('--trace', action='store_true', help='Enable trace headers and print trace ID.')
    parser.add_argument(
        '--webhook-id',
        default=WEBHOOK_ID,
        help=f'Webhook ID to check (default: {WEBHOOK_ID})'
    )
    return parser.parse_args()

def check_webhook_subscription(webhook_id, consumer_key, consumer_secret, access_token, access_token_secret, trace_enabled):
    """Checks the subscription status for a given webhook ID."""

    # --- Construct the URL ---
    endpoint_path = f"/account_activity/webhooks/{webhook_id}/subscriptions/all"
    resource_url = f"{API_BASE_URL}{endpoint_path}"

    # --- Set up OAuth 1.0a Authentication ---
    oauth = OAuth1(
        client_key=consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
        signature_method='HMAC-SHA1'
    )

    # --- Prepare Request Headers ---
    request_headers = {
        "Dtab-Local": ";".join(STAGING1_DTAB_OVERRIDES),
        "X-TFE-Experiment-environment": "staging1",
        "X-Decider-Overrides": "tfe_route:des_apiservice_staging1=on",
        "Content-Type": "application/json",
    }
    if trace_enabled:
        print("Trace flag enabled. Adding X-B3-Flags header.")
        request_headers["X-B3-Flags"] = "1"

    # --- Make the API Request ---
    print(f"Making GET request to: {resource_url}")
    try:
        response = requests.get(
            url=resource_url,
            headers=request_headers,
            auth=oauth
        )

        # --- Process the Response ---
        print(f"Status Code: {response.status_code}")

        if trace_enabled and 'x-transaction-id' in response.headers:
            print(f"Trace ID (x-transaction-id): {response.headers['x-transaction-id']}")

        if response.status_code == 204:
            print("Result: Success! (204 No Content) - The user has an active subscription for this webhook.")
        elif response.status_code == 404:
            print("Result: Not Found (404) - User may not have an active subscription, or the webhook ID might be incorrect.")
        elif response.status_code == 401:
            print("Result: Unauthorized (401) - Check credentials and app permissions.")
        elif response.status_code == 403:
            print("Result: Forbidden (403) - Application might lack required permission level (e.g., whitelisting).")
        else:
            print(f"Result: Received unexpected status code {response.status_code}.")

        print("\nResponse Body:")
        try:
            print(response.json())
        except requests.exceptions.JSONDecodeError:
            print(response.text if response.text else "(No content)")

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred during the request: {e}")
        sys.exit(1) # Exit with error code if request fails

def main():
    """Main execution function."""
    args = parse_arguments()

    # Use environment variables or fall back to defaults for credentials
    # This encourages using environment variables for sensitive data
    consumer_key = os.environ.get("CONSUMER_KEY", CONSUMER_KEY)
    consumer_secret = os.environ.get("CONSUMER_SECRET", CONSUMER_SECRET)
    access_token = os.environ.get("ACCESS_TOKEN", ACCESS_TOKEN)
    access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET", ACCESS_TOKEN_SECRET)

    # Basic check if credentials seem present (can be improved)
    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        print("Error: Missing one or more API credentials. ", file=sys.stderr)
        print("Please set CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, and ACCESS_TOKEN_SECRET environment variables or update the script.", file=sys.stderr)
        sys.exit(1)

    check_webhook_subscription(
        webhook_id=args.webhook_id,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        trace_enabled=args.trace
    )

if __name__ == "__main__":
    main()

