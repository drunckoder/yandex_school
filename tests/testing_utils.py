import logging
from typing import Tuple, Any

from flask.testing import FlaskClient
from flask.wrappers import Response

logger = logging.getLogger(__name__)


def make_citizen(**kwargs):
    result = {
        "citizen_id": 1,
        "town": "Москва",
        "street": "Льва Толстого",
        "building": "16к7стр5",
        "apartment": 7,
        "name": "Иванов Иван Иванович",
        "birth_date": "26.12.1986",
        "gender": "male",
        "relatives": []
    }
    for k, v in kwargs.items():
        if k not in result.keys():
            logger.warning(f'Key {k} should not be in Citizen entity! Must be a typo!')
        result[k] = v
    return result


def _send_request(client: FlaskClient, method: str, query: str, body=None) -> Tuple[int, Any]:
    """
    Composes and sends request to server
    :param client: an instance of flask.testing.FlaskClient to make http requests
    :param method: http method of the request
    :param query: http query of the request
    :param body: [OPTIONAL] json serializable object - request body
    :return: Tuple[response_status_code, response_json]
    """
    logging.info(f'{method} {query}')
    logging.info(body)
    response: Response = getattr(client, method)(query, json=body)
    logging.info(response.status_code)
    logging.info(response.json)
    return response.status_code, response.json


def send_create_import_request(client: FlaskClient, body) -> Tuple[int, Any]:
    """
    Send post request to /imports
    :param client: an instance of flask.testing.FlaskClient to make http requests
    :param body: json serializable object - request body
    :return: Tuple[response_status_code, response_json]
    """
    query = '/imports'
    return _send_request(client, 'post', query, body)


def send_patch_citizen_request(client: FlaskClient, import_id: int, citizen_id: int, body) -> Tuple[int, Any]:
    """
    Send patch request to /imports/$import_id/citizens/$citizen_id
    :param client: an instance of flask.testing.FlaskClient to make http requests
    :param import_id: query parameter
    :param citizen_id: query parameter
    :param body: json serializable object - request body
    :return: Tuple[response_status_code, response_json]
    """
    query = f'/imports/{import_id}/citizens/{citizen_id}'
    return _send_request(client, 'patch', query, body)


def send_get_citizens_request(client: FlaskClient, import_id: int) -> Tuple[int, Any]:
    """
    Send get request to /imports/$import_id/citizens/
    :param client: an instance of flask.testing.FlaskClient to make http requests
    :param import_id: query parameter
    :return: Tuple[response_status_code, response_json]
    """
    query = f'/imports/{import_id}/citizens'
    return _send_request(client, 'get', query)


def send_get_birthdays_request(client: FlaskClient, import_id: int) -> Tuple[int, Any]:
    """
    Send get request to /imports/$import_id/citizens/birthdays
    :param client: an instance of flask.testing.FlaskClient to make http requests
    :param import_id: query parameter
    :return: Tuple[response_status_code, response_json]
    """
    query = f'/imports/{import_id}/citizens/birthdays'
    return _send_request(client, 'get', query)


def send_get_ages_request(client: FlaskClient, import_id: int) -> Tuple[int, Any]:
    """
    Send get request to /imports/$import_id/towns/stat/percentile/age
    :param client: an instance of flask.testing.FlaskClient to make http requests
    :param import_id: query parameter
    :return: Tuple[response_status_code, response_json]
    """
    query = f'/imports/{import_id}/towns/stat/percentile/age'
    return _send_request(client, 'get', query)
