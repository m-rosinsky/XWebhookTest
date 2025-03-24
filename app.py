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

# Defines a route for the GET request
@app.route('/webhooks/twitter', methods=['GET'])
def webhook_challenge():
  crc_token = request.args.get('crc_token')
  if crc_token is None:
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

  if args.debug:
    app.run(debug=True)
  else:
    serve(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':
  main()
