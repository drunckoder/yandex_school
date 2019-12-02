import logging

import pytest
from flask.testing import FlaskClient

from tests.testing_utils import send_create_import_request, make_citizen
from yandex_school import db
from yandex_school.app import app
from yandex_school.config import DB_LOGIN, DB_PASSWORD, DB_URL, DB_NAME

logger = logging.getLogger(__name__)


# TODO: check self relationship

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client: FlaskClient = app.test_client()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_LOGIN}:{DB_PASSWORD}@{DB_URL}/{DB_NAME}_test'
    db.drop_all()
    db.create_all()
    yield client


def test_malformed_requests(client: FlaskClient):
    # empty dict
    body = {}
    status, data = send_create_import_request(client, body)
    assert status == 400

    # empty citizens list
    body = {'citizens': []}
    status, data = send_create_import_request(client, body)
    assert status == 400

    # empty citizen
    body = {'citizens': [{}]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_missing_citizen_fields(client: FlaskClient):
    bodies = []

    for key in make_citizen().keys():
        bad_citizen = make_citizen()
        del bad_citizen[key]
        bodies.append({'citizens': [bad_citizen]})

    assert all([send_create_import_request(client, body)[0] == 400 for body in bodies])


def test_unexistent_relative(client: FlaskClient):
    bad_citizen = make_citizen(relatives=[2])
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_relationships_are_not_mutual(client: FlaskClient):
    bad_citizen1 = make_citizen(relatives=[2])
    bad_citizen2 = make_citizen(citizen_id=2, relatives=[])
    body = {'citizens': [bad_citizen1, bad_citizen2]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_duplicate_ids(client: FlaskClient):
    body = {'citizens': [make_citizen(), make_citizen()]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_unexistent_date(client: FlaskClient):
    bad_citizen = make_citizen(birth_date='01.13.2019')
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_wrong_date_format(client: FlaskClient):
    bad_citizen = make_citizen(birth_date='01.1.2019')
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_wrong_citizen_id(client: FlaskClient):
    bad_citizen = make_citizen(citizen_id=0)
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400

    bad_citizen = make_citizen(citizen_id=-1)
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_wrong_citizen_id_data_type(client: FlaskClient):
    bad_citizen = make_citizen(citizen_id='a')
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400

    bad_citizen = make_citizen(citizen_id=None)
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_wrong_town_data_type(client: FlaskClient):
    bad_citizen = make_citizen(town=None)
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_wrong_street_data_type(client: FlaskClient):
    bad_citizen = make_citizen(street=None)
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_wrong_building_data_type(client: FlaskClient):
    bad_citizen = make_citizen(building=None)
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_wrong_apartment_data_type(client: FlaskClient):
    bad_citizen = make_citizen(apartment=None)
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400

    bad_citizen = make_citizen(apartment='a')
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_wrong_name_data_type(client: FlaskClient):
    bad_citizen = make_citizen(name=None)
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_wrong_birth_date_data_type(client: FlaskClient):
    bad_citizen = make_citizen(birth_date=None)
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400

    bad_citizen = make_citizen(birth_date='b')
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400

    bad_citizen = make_citizen(birth_date='12.12.201a')
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_wrong_gender_data_type(client: FlaskClient):
    bad_citizen = make_citizen(gender=None)
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_wrong_relatives_data_type(client: FlaskClient):
    bad_citizen = make_citizen(relatives='a')
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400

    bad_citizen = make_citizen(relatives=["a"])
    body = {'citizens': [bad_citizen]}
    status, data = send_create_import_request(client, body)
    assert status == 400


def test_good_citizens(client: FlaskClient):
    body = {'citizens': [make_citizen()]}
    status, data = send_create_import_request(client, body)
    assert status == 201


def test_good_citizens_relationships(client: FlaskClient):
    good_citizen1 = make_citizen(citizen_id=1, relatives=[2])
    good_citizen2 = make_citizen(citizen_id=2, relatives=[1])
    body = {'citizens': [good_citizen1, good_citizen2]}
    status, data = send_create_import_request(client, body)
    assert status == 201
