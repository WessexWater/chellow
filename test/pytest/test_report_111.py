import chellow.reports.report_111

from utils import (
    insert_batch, insert_contract, insert_participant, insert_party,
    insert_supplier_market_role, match,
)


# End to end tests

def test_ete_error_message_for_invalid_bill_id(client, sess):
    data = {
        'bill_id': "0",
    }
    response = client.get('/reports/111', data=data)

    match(response, 404, [])


# HTTP level tests

def test_http_supplier_batch_with_mpan_cores(mocker, client, sess):
    market_role_id = insert_supplier_market_role(sess)
    participant_id = insert_participant(sess)
    party_id = insert_party(
        sess, participant_id=participant_id, market_role_id=market_role_id)
    contract_id = insert_contract(
        sess, market_role_id=market_role_id, party_id=party_id)
    batch_id = insert_batch(sess, contract_id)
    sess.commit()
    MockThread = mocker.patch('chellow.reports.report_111.threading.Thread')

    data = {
        'batch_id': str(batch_id),
        'mpan_cores': "22 1065 3921 534",
    }
    response = client.get('/reports/111', data=data)

    match(response, 303, [])

    expected_args = (
        batch_id,
        None,
        None,
        None,
        None,
        None,
        ['22 1065 3921 534'],
        '_batch_005'
    )

    MockThread.assert_called_with(
        target=chellow.reports.report_111.content,
        args=expected_args)


# Worker level tests
