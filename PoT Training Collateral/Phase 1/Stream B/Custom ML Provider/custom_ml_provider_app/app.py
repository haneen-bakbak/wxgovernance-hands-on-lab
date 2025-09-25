from flask import Flask, request, abort, jsonify
from flask import Flask
from flask_httpauth import HTTPBasicAuth
import requests
import json
import os

app = Flask(__name__)
auth = HTTPBasicAuth()

with open("credentials.json") as creds:
    CREDENTIALS= json.load(creds)

os.environ["DATABRICKS_TOKEN"] = CREDENTIALS['databricks_token']

users = {
    CREDENTIALS['username']: CREDENTIALS['password']
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users.get(username) == "password":
        return username

@app.route('/')
@auth.login_required
def index():
    return jsonify("Hello, {}!".format(auth.current_user()))

    
@app.route('/predictions', methods=['POST'])
@auth.login_required
def score_model():
    if not request.json:
        abort(400)
        
    invocations_url = 'https://adb-3528367123873887.7.azuredatabricks.net/serving-endpoints/amazonstock/invocations'

    scoring_payload= request.json
    
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"
    headers["Authorization"] = "Bearer {}".format(os.environ["DATABRICKS_TOKEN"])        
    
    input_fields = scoring_payload['fields']
    input_values = scoring_payload['values']

    print("\n\ninput_values: \n")
    print(input_values)
    print("\n\n")

    # construct the scoring payload for ADB Model Deployment
    # get the response
    response = requests.post(invocations_url, headers=headers, json = {"inputs": input_values}, verify=False)
    response_json = response.json()

    # # construct the response to what WML Python Function should send back.
    transformed_response = {
        'values': [[round(value[0], 4)] for value in response_json['predictions']],
        'fields': ['prediction']
    }           
    
    print("\n\n Constructed Response:: \n")
    print(transformed_response)
    print("\n\n")

    return jsonify(transformed_response)


if __name__ == '__main__':
    app.run(port=9443, debug=True)