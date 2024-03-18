from tempfile import TemporaryDirectory

from flask.testing import FlaskClient

from jinja2 import Environment, PackageLoader, select_autoescape

import pg8000

import pytest

from requests.auth import _basic_auth_str

from sqlalchemy import text


import chellow.models
from chellow import create_app
from chellow.models import RSession, Session, User, UserRole, stop_sqlalchemy


@pytest.fixture
def fresh_db():
    stop_sqlalchemy()
    config = chellow.models.config
    database = config["PGDATABASE"]
    with pg8000.connect(
        config["PGUSER"],
        host=config["PGHOST"],
        database="postgres",
        port=int(config["PGPORT"]),
        password=config["PGPASSWORD"],
    ) as con:
        cursor = con.cursor()
        con.rollback()
        con.autocommit = True
        cursor.execute(f"DROP DATABASE IF EXISTS {database};")
        cursor.execute(f"CREATE DATABASE {database} ENCODING 'UTF8';")


@pytest.fixture
def app(fresh_db):
    chellow.e.bill_importer.import_id = 0
    chellow.e.bill_importer.imports.clear()
    with TemporaryDirectory() as td:
        yield create_app(testing=True, instance_path=td)


@pytest.fixture
def raw_client(app):
    return app.test_client()


class CustomClient(FlaskClient):
    def open(self, *args, **kwargs):
        if "headers" in kwargs:
            headers = kwargs["headers"]
        else:
            headers = kwargs["headers"] = {}

        headers["Authorization"] = _basic_auth_str("admin@example.com", "admin")
        return super().open(*args, **kwargs)


@pytest.fixture
def sess(app):
    sess = Session()
    yield sess
    sess.close()


@pytest.fixture
def rsess(app):
    rsess = RSession()
    yield rsess
    rsess.close()


@pytest.fixture
def client(app, sess):
    app.test_client_class = CustomClient

    with app.test_client() as client:
        with app.app_context():
            user_role = UserRole.insert(sess, "editor")
            User.insert(sess, "admin@example.com", "admin", user_role, None)

            sess.execute(
                text(
                    "INSERT INTO market_role (code, description) "
                    "VALUES ('Z', 'Non-core Role')"
                )
            )
            sess.execute(
                text(
                    "INSERT INTO participant (code, name) " "VALUES ('NEUT', 'Neutral')"
                )
            )
            sess.execute(
                text(
                    "INSERT INTO party (market_role_id, participant_id, name, "
                    "valid_from, valid_to, dno_code) "
                    "VALUES (1, 1, 'Neutral Party', '2000-01-01', null, null)"
                )
            )
            sess.execute(
                text(
                    "INSERT INTO contract (name, charge_script, properties, "
                    "state, market_role_id, party_id, start_rate_script_id, "
                    "finish_rate_script_id) VALUES ('configuration', '{}', '{}', "
                    "'{}', 1, 1, null, null)"
                )
            )
            sess.execute(
                text(
                    "INSERT INTO rate_script "
                    "(contract_id, start_date, finish_date, "
                    "script) VALUES (1, '2020-01-01', '2020-01-31', '{}')"
                )
            )
            sess.execute(
                text(
                    "UPDATE contract set start_rate_script_id = 1, "
                    "finish_rate_script_id = 1 where id = 1;"
                )
            )
            sess.commit()

        yield client


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def jinja2_env():
    return Environment(
        loader=PackageLoader("../chellow/", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
