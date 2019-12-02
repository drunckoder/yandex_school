import logging

import pytest

from tests.testing_utils import make_citizen, send_create_import_request, \
    send_patch_citizen_request, send_get_citizens_request
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
    citizen_id = 1
    body = {'name': '1'}

    import_id = -1
    status, data = send_patch_citizen_request(client, import_id, citizen_id, body)
    assert status == 404

    import_id = 0
    status, data = send_patch_citizen_request(client, import_id, citizen_id, body)
    assert status == 404

    import_id = 1
    status, data = send_patch_citizen_request(client, import_id, citizen_id, body)
    assert status == 404


def test_patch_all_rows(client):
    citizens = [make_citizen(citizen_id=x) for x in range(1, 11)]
    body = {'citizens': citizens}
    status, data = send_create_import_request(client, body)
    assert status == 201

    import_id = data['data']['import_id']

    citizen_id = 3

    bodies = []

    for key in make_citizen().keys():
        if key == 'citizen_id':
            continue
        citizen_part = {key: make_citizen()[key]}
        bodies.append(citizen_part)

    assert all([send_patch_citizen_request(client, import_id, citizen_id, body)[0] == 200 for body in bodies])

    bodies = []

    for key in make_citizen().keys():
        if key == 'citizen_id':
            continue
        citizen_part = make_citizen()
        del citizen_part['citizen_id']
        del citizen_part[key]
        bodies.append(citizen_part)

    assert all([send_patch_citizen_request(client, import_id, citizen_id, body)[0] == 200 for body in bodies])


def test_patch_relationships(client):
    citizens = [make_citizen(citizen_id=x) for x in range(1, 11)]
    body = {'citizens': citizens}
    status, data = send_create_import_request(client, body)
    assert status == 201

    import_id = data['data']['import_id']

    citizen_id = 10
    body = {'relatives': []}
    status, data = send_patch_citizen_request(client, import_id, citizen_id, body)
    assert status == 200

    citizen_id = 10
    body = {'relatives': [1, 2, 3, 4, 5, 6, 7, 8, 9]}
    status, data = send_patch_citizen_request(client, import_id, citizen_id, body)
    assert status == 200

    citizen_id = 9
    body = make_citizen(relatives=[1, 2, 3, 4, 5, 6, 7, 8, 10])
    del body['citizen_id']
    status, data = send_patch_citizen_request(client, import_id, citizen_id, body)
    assert status == 200

    citizen_id = 10
    body = {'relatives': []}
    status, data = send_patch_citizen_request(client, import_id, citizen_id, body)
    assert status == 200

    citizen_id = 9
    body = make_citizen(relatives=[])
    del body['citizen_id']
    status, data = send_patch_citizen_request(client, import_id, citizen_id, body)
    assert status == 200
