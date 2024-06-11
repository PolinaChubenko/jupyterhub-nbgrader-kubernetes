from flask import Flask
import requests
from requests.exceptions import HTTPError

import os
import logging

admin_token = os.getenv("ADMIN_TOKEN")

app = Flask(__name__)

base_url = "https://jupyterhub.sunpixel.ru"
headers = {
    "Authorization": f"token {admin_token}",
}

@app.route('/collect/<course>/<assignment>', methods=['POST'])
def collect(course, assignment):
    url = base_url + f"/services/{course}/formgrader/api/assignment/{assignment}/collect"
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
    except HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')
        return {
            "success": False,
             "log": f'HTTP error occurred on manager request to jupyterhub'
        }
    except Exception as err:
        logging.error(f'Other error occurred: {err}')
        return {
            "success": False, 
            "log": f'Other error occurred on manager request to jupyterhub'
        }
    else:
        json_response = response.json()
        if json_response['success']:
            return {
                "success": True, 
                "log": "Submittion was collected by instructor"
            }
        else: 
            return json_response


@app.route('/autograde/<course>/<assignment>/<student>', methods=['POST'])
def autograde(course, assignment, student):
    url = base_url + f"/services/{course}/formgrader/api/submission/{assignment}/{student}/autograde"
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
    except HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')
        return {
            "success": False,
             "log": f'HTTP error occurred on manager request to jupyterhub'
        }
    except Exception as err:
        logging.error(f'Other error occurred: {err}')
        return {
            "success": False, 
            "log": f'Other error occurred on manager request to jupyterhub'
        }
    else:
        json_response = response.json()
        if json_response['success']:
            return {
                "success": True, 
                "log": "Submittion was autograded by instructor"
            }
        else: 
            return json_response


if __name__ == "__main__":
    app.run(host='0.0.0.0')
