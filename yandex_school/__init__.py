from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

from yandex_school.config import DB_URL, DB_LOGIN, DB_PASSWORD, DB_NAME

app = Flask(__name__)
api = Api(app)
cors = CORS(app, resources={r'/*': {'origins': '*'}})  # headache reducer

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_LOGIN}:{DB_PASSWORD}@{DB_URL}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # turning off an outdated feature

# TODO: experimental alchemy flags, might blame weird behavior on them
db = SQLAlchemy(app, engine_options={'echo': False}, session_options={'autoflush': False, 'expire_on_commit': False})
