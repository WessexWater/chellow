from chellow.utils import utc_datetime
import chellow.computer


def test_find_pair(mocker):
    sess = mocker.Mock()
    caches = {}
    is_forwards = True
    first_read = {
        'date': utc_datetime(2010, 1, 1),
        'reads': {},
        'msn': 'kh'
    }
    second_read = {
        'date': utc_datetime(2010, 2, 1),
        'reads': {},
        'msn': 'kh'
    }
    read_list = [first_read, second_read]
    pair = chellow.computer._find_pair(sess, caches, is_forwards, read_list)
    assert pair['start-date'] == utc_datetime(2010, 1, 1)


def test_find_hhs_empty_pairs(mocker):
    mocker.patch("chellow.computer.is_tpr", return_value=True)
    caches = {}
    sess = mocker.Mock()
    pairs = []
    chunk_start = utc_datetime(2010, 1, 1)
    chunk_finish = utc_datetime(2010, 1, 1)
    hhs = chellow.computer._find_hhs(
        caches, sess, pairs, chunk_start, chunk_finish)
    assert hhs == {
        utc_datetime(2010, 1, 1): {
            'msp-kw': 0, 'msp-kwh': 0, 'hist-kwh': 0, 'imp-msp-kvar': 0,
            'imp-msp-kvarh': 0, 'exp-msp-kvar': 0, 'exp-msp-kvarh': 0,
            'tpr': '00001'
        }
    }


def test_find_hhs_two_pairs(mocker):
    mocker.patch("chellow.computer.is_tpr", return_value=True)
    caches = {}
    sess = mocker.Mock()
    pairs = [
        {
            'start-date': utc_datetime(2010, 1, 1),
            'tprs': {
                '00001': 1
            }
        },
        {
            'start-date': utc_datetime(2010, 1, 1, 0, 30),
            'tprs': {
                '00001': 1
            }
        }
    ]
    chunk_start = utc_datetime(2010, 1, 1)
    chunk_finish = utc_datetime(2010, 1, 1, 0, 30)
    hhs = chellow.computer._find_hhs(
        caches, sess, pairs, chunk_start, chunk_finish)
    assert hhs == {
        utc_datetime(2010, 1, 1): {
            'msp-kw': 2.0, 'msp-kwh': 1.0, 'hist-kwh': 1.0, 'imp-msp-kvar': 0,
            'imp-msp-kvarh': 0, 'exp-msp-kvar': 0, 'exp-msp-kvarh': 0,
            'tpr': '00001'
        },
        utc_datetime(2010, 1, 1, 0, 30): {
            'msp-kw': 2.0, 'msp-kwh': 1.0, 'hist-kwh': 1.0, 'imp-msp-kvar': 0,
            'imp-msp-kvarh': 0, 'exp-msp-kvar': 0, 'exp-msp-kvarh': 0,
            'tpr': '00001'
        }
    }


def test_set_status(mocker):
    hhs = {
        utc_datetime(2012, 2, 1): {}
    }

    read_list = [
        {
            'date': utc_datetime(2012, 1, 1)
        }
    ]
    forecast_date = utc_datetime(2012, 3, 1)
    chellow.computer._set_status(hhs, read_list, forecast_date)
    assert hhs == {
        utc_datetime(2012, 2, 1): {
            'status': 'A'
        }
    }


def test_make_reads_forwards(mocker):
    is_forwards = True
    msn = 'k'
    read_a = {'date': utc_datetime(2018, 3, 10), 'msn': msn}
    read_b = {'date': utc_datetime(2018, 3, 13), 'msn': msn}
    prev_reads = iter([read_a])
    pres_reads = iter([read_b])
    actual = list(
        chellow.computer._make_reads(is_forwards, prev_reads, pres_reads))
    expected = [read_a, read_b]
    assert actual == expected


def test_make_reads_forwards_meter_change(mocker):
    is_forwards = True
    dt = utc_datetime(2018, 3, 1)
    read_a = {'date': dt, 'msn': 'a'}
    read_b = {'date': dt, 'msn': 'b'}
    prev_reads = iter([read_a])
    pres_reads = iter([read_b])
    actual = list(
        chellow.computer._make_reads(is_forwards, prev_reads, pres_reads))
    expected = [read_b, read_a]
    assert actual == expected


def test_make_reads_backwards(mocker):
    is_forwards = False
    msn = 'k'
    read_a = {'date': utc_datetime(2018, 3, 10), 'msn': msn}
    read_b = {'date': utc_datetime(2018, 3, 13), 'msn': msn}
    prev_reads = iter([read_a])
    pres_reads = iter([read_b])
    actual = list(
        chellow.computer._make_reads(is_forwards, prev_reads, pres_reads))
    expected = [read_b, read_a]
    assert actual == expected
