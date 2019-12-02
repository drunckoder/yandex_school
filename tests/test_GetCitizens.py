import logging

import pytest

from tests.testing_utils import make_citizen, send_create_import_request, send_get_citizens_request
from yandex_school import db
from yandex_school.app import app
from yandex_school.config import DB_LOGIN, DB_PASSWORD, DB_URL, DB_NAME

logger = logging.getLogger(__name__)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_LOGIN}:{DB_PASSWORD}@{DB_URL}/{DB_NAME}_test'
    db.drop_all()
    db.create_all()
    yield client


def test_bad_import_id(client):
    import_id = -1
    status, data = send_get_citizens_request(client, import_id)
    assert status == 404

    import_id = 0
    status, data = send_get_citizens_request(client, import_id)
    assert status == 404

    import_id = 1
    status, data = send_get_citizens_request(client, import_id)
    assert status == 404


def test_single_citizen(client):
    body = {'citizens': [make_citizen()]}
    status, data = send_create_import_request(client, body)
    assert status == 201

    import_id = data['data']['import_id']

    status, data = send_get_citizens_request(client, import_id)
    assert status == 200


def test_multiple_citizens(client):
    citizens = [make_citizen(citizen_id=x) for x in range(1, 11)]
    body = {'citizens': citizens}
    status, data = send_create_import_request(client, body)
    assert status == 201

    import_id = data['data']['import_id']

    status, data = send_get_citizens_request(client, import_id)
    assert status == 200
