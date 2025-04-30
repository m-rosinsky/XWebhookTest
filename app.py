from flask import Flask, request, jsonify
from flask_cors import CORS
from waitress import serve

import argparse
import base64
import hashlib
import hmac
import os
import json
import sys

app = Flask(__name__)

# /var/lib/tss/keys/mrosinsky/webhookapp/consumer_key
TWITTER_CONSUMER_SECRET = os.environ.get("TWITTER_CONSUMER_SECRET")
if TWITTER_CONSUMER_SECRET is None:
  print("Missing consumer secret. Ensure TWITTER_CONSUMER_SECRET env var is set.")
  sys.exit(1)

# Defines a route for the GET and POST requests.
@app.route('/webhooks/twitter', methods=['GET', 'POST'])
def webhook_challenge():
  # Handle GET request (CRC challenge)
  if request.method == 'GET':
    print(f"--- Received GET request from {request.remote_addr} ---")
    crc_token = request.args.get('crc_token')
    print(f"CRC Token received: {crc_token}")
    if crc_token is None:
      print("Error: No crc_token found in the request.")
      return json.dumps({'error': 'No crc_token'})

    # Creates HMAC SHA-256 hash from incomming token and your consumer secret.
    sha256_hash_digest = hmac.new(
      TWITTER_CONSUMER_SECRET.encode('utf-8'),
      msg=crc_token.encode('utf-8'),
      digestmod=hashlib.sha256
    ).digest()

    # Construct response data with base64 encoded hash.
    response = {
      'response_token': 'sha256=' + base64.b64encode(sha256_hash_digest).decode('utf-8')
    }

    # Returns properly formatted json response.
    return jsonify(response)

  # Handle POST request (Webhook event)
  elif request.method == 'POST':
    event_data = request.get_json()
    if event_data:
      print("--- Received Webhook Event ---")
      print(json.dumps(event_data, indent=2))
      print("-----------------------------")
    else:
      # Log if the request body wasn't JSON or was empty
      print("--- Received POST request with non-JSON or empty body ---")
      print(f"Body: {request.data.decode('utf-8')}")
      print("--------------------------------------------------------")

    # Return 200 OK
    return '', 200

  # Handle other methods if necessary (optional)
  else:
    print(f"--- Received unsupported method {request.method} from {request.remote_addr} ---")
    return 'Method Not Allowed', 405

def main():
  parser = argparse.ArgumentParser(
    description='Webhook app'
  )

  parser.add_argument(
    '--debug',
    action='store_true',
    help='Run without a WSGI server',
  )
  args = parser.parse_args()

  print("--- Starting Webhook App ---")
  print(f"Using TWITTER_CONSUMER_SECRET from environment variable.")

  if args.debug:
    print("Running in DEBUG mode (Flask development server)")
    app.run(debug=True)
  else:
    host = '0.0.0.0'
    port = 8080
    print(f"Running with Waitress WSGI server on {host}:{port}")
    serve(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':
  main()
