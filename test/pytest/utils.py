import re


def match(response, status_code, patterns):
    response_str = response.get_data(as_text=True)

    assert response.status_code == status_code, response_str

    for regex in patterns:
        assert re.search(regex, response_str, flags=re.MULTILINE + re.DOTALL)


def insert_participant(sess, code="FUSE", name="Fusion"):
    params = {
        'code': code,
        'name': name
    }
    results = sess.execute(
        "INSERT INTO participant (id, code, name) VALUES "
        "(DEFAULT, :code, :name) RETURNING id", params)
    return next(results)[0]


def insert_market_role(sess, code, description):
    params = {
        'code': code,
        'description': description
    }
    results = sess.execute(
        "INSERT INTO market_role (id, code, description) "
        "VALUES (DEFAULT, :code, :description) RETURNING id", params)
    return next(results)[0]


def insert_supplier_market_role(sess):
    return insert_market_role(sess, 'X', 'Supplier')


def insert_party(
        sess, market_role_id=None, participant_id=None, name="Fusion Energy",
        valid_from='2000-01-01', valid_to=None, dno_code=None):
    params = {
        'market_role_id': market_role_id,
        'participant_id': participant_id,
        'name': name,
        'valid_from': valid_from,
        'valid_to': valid_to,
        'dno_code': dno_code,
    }
    results = sess.execute(
        "INSERT INTO party (market_role_id, participant_id, name, "
        "valid_from, valid_to, dno_code) "
        "VALUES (:market_role_id, :participant_id, :name, :valid_from, "
        ":valid_to, :dno_code) RETURNING id", params)
    return next(results)[0]


def insert_contract(
        sess, market_role_id=None, party_id=None, contract_name="2020 Fusion",
        start_date='2020-01-01', finish_date=None, charge_script='{}',
        properties='{}', state='{}'):

    params = {
        'contract_name': contract_name,
        'charge_script': charge_script,
        'properties': properties,
        'state': state,
        'market_role_id': market_role_id,
        'party_id': party_id
    }
    results = sess.execute(
        "INSERT INTO contract (id, name, charge_script, properties, "
        "state, market_role_id, party_id, start_rate_script_id, "
        "finish_rate_script_id) VALUES (DEFAULT, :contract_name, "
        ":charge_script, :properties, :state, :market_role_id, :party_id, "
        "null, null) RETURNING id", params)
    contract_id = next(results)[0]

    params = {
        'contract_id': contract_id,
        'start_date': start_date,
        'finish_date':  finish_date,
    }
    results = sess.execute(
        "INSERT INTO rate_script (id, contract_id, start_date, finish_date, "
        "script) VALUES "
        "(DEFAULT, :contract_id, :start_date, :finish_date, '{}') "
        "RETURNING id", params)
    rate_script_id = next(results)[0]

    params = {
        'contract_id': contract_id,
        'rate_script_id': rate_script_id
    }
    sess.execute(
        "UPDATE contract set start_rate_script_id = :rate_script_id, "
        "finish_rate_script_id = :rate_script_id where id = :contract_id;",
        params)
    return contract_id


def insert_batch(
        sess, contract_id=None, reference="005", description="Autumn"):
    params = {
        'contract_id': contract_id,
        'reference': reference,
        'description': description,
    }
    results = sess.execute(
        "INSERT INTO batch (id, contract_id, reference, description) "
        "VALUES (DEFAULT, :contract_id, :reference, :description) "
        "RETURNING id", params)
    return next(results)[0]
