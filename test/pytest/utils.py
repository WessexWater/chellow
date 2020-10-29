import re
from decimal import Decimal

from zish import dumps


def match(response, status_code, *patterns):
    response_str = response.get_data(as_text=True)

    assert response.status_code == status_code, response_str

    for regex in patterns:
        assert re.search(
            regex, response_str, flags=re.MULTILINE + re.DOTALL), response_str


def insert_bill_types(sess):
    for code, description in (
            ("F", "Final"),
            ("N", "Normal"),
            ("W", "Withdrawn")):
        insert_bill_type(sess, code, description)


def insert_bill_type(sess, code, description):
    params = {
        'code': code,
        'description': description,
    }
    results = sess.execute(
        "INSERT INTO bill_type (id, code, description) VALUES "
        "(DEFAULT, :code, :description) RETURNING id", params)
    return next(results)[0]


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


def insert_g_contract(
        sess, name="Hydrogen 2020", charge_script='{}', properties='{}',
        state="{}", start_date="2020-01-01", finish_date=None):
    params = {
        'name': name,
        'charge_script': charge_script,
        'properties': properties,
        'state': state,
    }
    results = sess.execute(
        "INSERT INTO g_contract (id, name, charge_script, properties, state, "
        "start_g_rate_script_id, finish_g_rate_script_id) "
        "VALUES (DEFAULT, :name, :charge_script, :properties, :state, "
        "NULL, NULL) RETURNING id", params)
    g_contract_id = next(results)[0]

    params = {
        'g_contract_id': g_contract_id,
        'start_date': start_date,
        'finish_date':  finish_date,
    }
    results = sess.execute(
        "INSERT INTO g_rate_script (id, g_contract_id, start_date, "
        "finish_date, script) VALUES "
        "(DEFAULT, :g_contract_id, :start_date, :finish_date, '{}') "
        "RETURNING id", params)
    g_rate_script_id = next(results)[0]

    params = {
        'g_contract_id': g_contract_id,
        'g_rate_script_id': g_rate_script_id
    }
    sess.execute(
        "UPDATE g_contract set start_g_rate_script_id = :g_rate_script_id, "
        "finish_g_rate_script_id = :g_rate_script_id "
        "where id = :g_contract_id;", params)
    return g_contract_id


def insert_g_dn(sess, code='EE', name='East of England'):

    params = {
        'code': code,
        'name': name,
    }

    results = sess.execute(
        "INSERT INTO g_dn (id, code, name) VALUES "
        "(DEFAULT, :code, :name) RETURNING id", params)
    return next(results)[0]


def insert_g_ldz(sess, g_dn_id=None, code='EA'):

    params = {
        'g_dn_id': g_dn_id,
        'code': code,
    }

    results = sess.execute(
        "INSERT INTO g_ldz (id, g_dn_id, code) VALUES "
        "(DEFAULT, :g_dn_id, :code) RETURNING id", params)
    return next(results)[0]


def insert_g_exit_zone(sess, g_ldz_id=None, code='EA1'):

    params = {
        'g_ldz_id': g_ldz_id,
        'code': code,
    }

    results = sess.execute(
        "INSERT INTO g_exit_zone (id, g_ldz_id, code) VALUES "
        "(DEFAULT, :g_ldz_id, :code) RETURNING id", params)
    return next(results)[0]


def insert_g_units(sess):
    for code, description, factor_str in (
            ("MCUF", "Thousands of cubic feet", '28.3'),
            ("HCUF", "Hundreds of cubic feet", '2.83'),
            ("TCUF", "Tens of cubic feet", '0.283'),
            ("OCUF", "One cubic foot", '0.0283'),
            ("M3", "Cubic metres", '1'),
            ("HM3", "Hundreds of cubic metres", '100'),
            ("TM3", "Tens of cubic metres", '10'),
            ("NM3", "Tenths of cubic metres", '0.1')):
        insert_g_unit(sess, code, description, Decimal(factor_str))


def insert_g_unit(sess, code, description, factor):

    params = {
        'code': code,
        'description': description,
        'factor': factor,
    }

    results = sess.execute(
        "INSERT INTO g_unit (id, code, description, factor) VALUES "
        "(DEFAULT, :code, :description, :factor) RETURNING id", params)
    return next(results)[0]


def insert_g_supply(
        sess, mprn='hhk 53488', name='Iseult', g_exit_zone_id=None, note=''):

    params = {
        'mprn': mprn,
        'name': name,
        'g_exit_zone_id': g_exit_zone_id,
        'note': note,
    }

    results = sess.execute(
        "INSERT INTO g_supply (id, mprn, name, g_exit_zone_id, "
        "note) VALUES "
        "(DEFAULT, :mprn, :name, :g_exit_zone_id, :note"
        ") RETURNING id", params)
    return next(results)[0]


def select_g_unit_id(sess, code='M3'):
    params = {
        'code': code,
    }

    results = sess.execute("SELECT id from g_unit where code = :code", params)
    try:
        return next(results)[0]
    except StopIteration:
        raise Exception(f"There isn't a g_unit with code {code}.")


def insert_g_reading_frequencies(sess):
    for code, description in (('A', "Annual"), ('M', "Monthly")):
        insert_g_reading_frequency(sess, code, description)


def insert_g_reading_frequency(sess, code, description):

    params = {
        'code': code,
        'description': description,
    }

    results = sess.execute(
        "INSERT INTO g_reading_frequency (id, code, description) VALUES "
        "(DEFAULT, :code, :description) RETURNING id", params)
    return next(results)[0]


def select_g_reading_frequency_id(sess, code='M'):
    params = {
        'code': code,
    }

    results = sess.execute(
        "SELECT id from g_reading_frequency where code = :code", params)
    try:
        return next(results)[0]
    except StopIteration:
        raise Exception(f"There isn't a g_reading_frequency with code {code}.")


def insert_g_era(
        sess, g_supply_id=None, start_date='2020-01-01', finish_date=None,
        msn='ghnghkky', correction_factor=1, g_unit_code='M3',
        g_contract_id=None, account='hgkr5l',
        g_reading_frequency_code='M'):

    g_unit_id = select_g_unit_id(sess, code=g_unit_code)
    g_reading_frequency_id = select_g_reading_frequency_id(
        sess, code=g_reading_frequency_code)

    params = {
        'g_supply_id': g_supply_id,
        'start_date': start_date,
        'finish_date': finish_date,
        'msn': msn,
        'correction_factor': correction_factor,
        'g_unit_id': g_unit_id,
        'g_contract_id': g_contract_id,
        'account': account,
        'g_reading_frequency_id': g_reading_frequency_id,
    }

    results = sess.execute(
        "INSERT INTO g_era (id, g_supply_id, start_date, finish_date, "
        "msn, correction_factor, g_unit_id, g_contract_id, account, "
        "g_reading_frequency_id) VALUES "
        "(DEFAULT, :g_supply_id, :start_date, :finish_date, :msn, "
        ":correction_factor, :g_unit_id, :g_contract_id, :account, "
        ":g_reading_frequency_id) RETURNING id", params)
    return next(results)[0]


def insert_g_read_types(sess):
    for code, desc in (
            ("A", "Actual"),
            ("C", "Customer"),
            ("E", "Estimated"),
            ("S", "Deemed read")):
        insert_g_read_type(sess, code, desc)


def insert_g_read_type(sess, code, description):
    params = {
        'code': code,
        'description': description,
    }
    results = sess.execute(
        "INSERT INTO g_read_type (id, code, description) "
        "VALUES (DEFAULT, :code, :description) RETURNING id", params)
    return next(results)[0]


def select_g_read_type_id(sess, code='M3'):
    params = {
        'code': code,
    }

    results = sess.execute(
        "SELECT id from g_read_type where code = :code", params)
    try:
        return next(results)[0]
    except StopIteration:
        raise Exception(f"There isn't a g_read_type with code {code}.")


def insert_g_batch(
        sess, g_contract_id=None, reference="005", description="Autumn"):
    params = {
        'g_contract_id': g_contract_id,
        'reference': reference,
        'description': description,
    }
    results = sess.execute(
        "INSERT INTO g_batch (id, g_contract_id, reference, description) "
        "VALUES (DEFAULT, :g_contract_id, :reference, :description) "
        "RETURNING id", params)
    return next(results)[0]


def insert_g_bill(
        sess, g_batch_id=None, g_supply_id=None, bill_type_id=None,
        reference="ref_4", account="Upper_Hamlet",
        issue_date="2020-04-12 00:00", start_date="2020-05-01 00:00",
        finish_date="2020-05-31 23:30", kwh=Decimal('85'),
        net=Decimal('60.30'), vat=Decimal('15.60'), gross=Decimal('80.00'),
        raw_lines='', breakdown=None):

    params = {
        'g_batch_id': g_batch_id,
        'g_supply_id': g_supply_id,
        'bill_type_id': bill_type_id,
        'reference': reference,
        'account': account,
        'issue_date': issue_date,
        'start_date': start_date,
        'finish_date': finish_date,
        'kwh': kwh,
        'net': net,
        'vat': vat,
        'gross': gross,
        'raw_lines': raw_lines,
        'breakdown': '{}' if breakdown is None else dumps(breakdown)
    }

    results = sess.execute(
        "INSERT INTO g_bill (id, g_batch_id, g_supply_id, bill_type_id, "
        "reference, account, issue_date, start_date, finish_date, kwh, "
        "net, vat, gross, raw_lines, breakdown) VALUES "
        "(DEFAULT, :g_batch_id, :g_supply_id, :bill_type_id, :reference, "
        ":account, :issue_date, :start_date, :finish_date, :kwh, :net, :vat, "
        ":gross, :raw_lines, :breakdown) RETURNING id", params)
    return next(results)[0]


def insert_g_read(
        sess, g_bill_id=None, msn="hgjsdehtg", g_unit_code='M3',
        correction_factor=1, calorific_value=1, prev_date='2020-01-01',
        prev_value=208, prev_type_code='E', pres_date='2020-01-31 23:30',
        pres_value=509, pres_type_code='A'):

    g_unit_id = select_g_unit_id(sess, code=g_unit_code)
    prev_type_id = select_g_read_type_id(sess, code=prev_type_code)
    pres_type_id = select_g_read_type_id(sess, code=pres_type_code)

    params = {
        'g_bill_id': g_bill_id,
        'msn': msn,
        'g_unit_id': g_unit_id,
        'correction_factor': correction_factor,
        'calorific_value': calorific_value,
        'prev_date': prev_date,
        'prev_value': prev_value,
        'prev_type_id': prev_type_id,
        'pres_date': pres_date,
        'pres_value': pres_value,
        'pres_type_id': pres_type_id,
    }

    results = sess.execute(
        "INSERT INTO g_register_read (id, g_bill_id, msn, g_unit_id, "
        "correction_factor, calorific_value, prev_date, prev_value, "
        "prev_type_id, pres_date, pres_value, pres_type_id) VALUES "
        "(DEFAULT, :g_bill_id, :msn, :g_unit_id, :correction_factor, "
        ":calorific_value, :prev_date, :prev_value, :prev_type_id, "
        ":pres_date, :pres_value, :pres_type_id) RETURNING id", params)
    return next(results)[0]
