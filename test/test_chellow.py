from chellow import create_app


def test_create_app(fresh_db):
    create_app()
