from flask import Flask
import requests
from requests.exceptions import HTTPError

import os
import logging

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
APRICOT_TOKEN = "581d2984-1dc4-4fc3-92d2-7dc1c1b18708"

app = Flask(__name__)

BASE_HUB_URL = "https://jupyterhub.sunpixel.ru"
BASE_APRICOT_URL = "https://jupyterhub.sunpixel.ru"
JUPYTERHUB_HEADERS = {
    "Authorization": f"token {ADMIN_TOKEN}",
}
APRICOT_HEADERS = {
    "Content-Type": "application/json",
}

@app.route('/collect/<course>/<assignment>', methods=['POST'])
def collect(course, assignment):
    url = BASE_HUB_URL + f"/services/{course}/formgrader/api/assignment/{assignment}/collect"
    try:
        response = requests.post(url, headers=JUPYTERHUB_HEADERS)
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
    url = BASE_HUB_URL + f"/services/{course}/formgrader/api/submission/{assignment}/{student}/autograde"
    try:
        response = requests.post(url, headers=JUPYTERHUB_HEADERS)
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


@app.route('/send_checker/<course>/<assignment>/<student>', methods=['POST'])
def send_checker(course, assignment, student):
    url = BASE_APRICOT_URL + f"/app/external_submit"
    data = {
        "token": APRICOT_TOKEN,
        "gitlab_login": student,
        "course_slug": course,
        "link": student,
        "task_slug": assignment,
    }
    try:
        response = requests.post(url, data=data, headers=APRICOT_HEADERS)
        response.raise_for_status()
    except HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')
        return {
            "success": False,
             "log": f'HTTP error occurred on manager request to apricot'
        }
    except Exception as err:
        logging.error(f'Other error occurred: {err}')
        return {
            "success": False, 
            "log": f'Other error occurred on manager request to apricot'
        }
    else:
        json_response = response.json()
        if json_response['success']:
            return {
                "success": True, 
                "log": "Submittion was send to apricot for long validation"
            }
        else: 
            return json_response


if __name__ == "__main__":
    app.run(host='0.0.0.0')
