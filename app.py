from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

@app.route('/ping')
def ping():
    return jsonify({"status": "true"}), 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
