import chellow.g_engine
from chellow.utils import utc_datetime


def test_find_hhs_pairs_before_after_chunk_finish(mocker):
    """If there's a meter change, a pair can start after the end of the chunk.
    here we test the case for a pair before and after the chunk finish.
    """
    mocker.patch("chellow.g_engine.find_cv", return_value=(39, 39))
    sess = mocker.Mock()
    caches = {}
    hist_g_era = mocker.Mock()
    hist_g_era.correction_factor = 1
    hist_g_era.g_unit = mocker.Mock()
    hist_g_era.g_unit.code = "M3"
    hist_g_era.g_unit.factor = 1

    pairs = [
        {"start-date": utc_datetime(2010, 1, 1), "units": 1},
        {"start-date": utc_datetime(2010, 1, 1, 0, 30), "units": 1},
    ]
    chunk_start = utc_datetime(2010, 1, 1)
    chunk_finish = utc_datetime(2010, 1, 1)
    g_cv_id = 0
    g_ldz_code = "SW"
    hhs = chellow.g_engine._find_hhs(
        sess, caches, hist_g_era, pairs, chunk_start, chunk_finish, g_cv_id, g_ldz_code
    )
    assert hhs == {
        utc_datetime(2010, 1, 1): {
            "unit_code": "M3",
            "unit_factor": 1.0,
            "units_consumed": 1,
            "correction_factor": 1.0,
            "calorific_value": 39,
            "avg_cv": 39,
        }
    }

    assert pairs == [
        {
            "start-date": utc_datetime(2010, 1, 1),
            "units": 1,
            "finish-date": utc_datetime(2010, 1, 1),
        },
    ]


def test_find_hhs_pair_after_chunk_finish(mocker):
    """If there's a meter change, a pair can start after the end of the chunk.
    Here we test for a single pair after the chunk finish.
    """
    mocker.patch("chellow.g_engine.find_cv", return_value=(39, 39))
    sess = mocker.Mock()
    caches = {}
    hist_g_era = mocker.Mock()
    hist_g_era.correction_factor = 1
    hist_g_era.g_unit = mocker.Mock()
    hist_g_era.g_unit.code = "M3"
    hist_g_era.g_unit.factor = 1

    pairs = [{"start-date": utc_datetime(2010, 1, 1, 0, 30), "units": 1}]
    chunk_start = utc_datetime(2010, 1, 1)
    chunk_finish = utc_datetime(2010, 1, 1)
    g_cv_id = 0
    g_ldz_code = "SW"
    hhs = chellow.g_engine._find_hhs(
        sess, caches, hist_g_era, pairs, chunk_start, chunk_finish, g_cv_id, g_ldz_code
    )
    assert hhs == {
        utc_datetime(2010, 1, 1): {
            "unit_code": "M3",
            "unit_factor": 1.0,
            "units_consumed": 1,
            "correction_factor": 1.0,
            "calorific_value": 39,
            "avg_cv": 39,
        }
    }

    assert pairs == [
        {
            "start-date": utc_datetime(2010, 1, 1),
            "units": 1,
            "finish-date": utc_datetime(2010, 1, 1),
        },
    ]
