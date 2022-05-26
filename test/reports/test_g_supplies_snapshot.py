import csv
from io import StringIO

import chellow.reports.report_g_supplies_snapshot
from chellow.models import (
    GContract,
    GDn,
    GReadingFrequency,
    GUnit,
    MarketRole,
    Participant,
    Site,
    insert_g_reading_frequencies,
    insert_g_units,
)
from chellow.utils import utc_datetime


def test_supply(mocker, sess, client):
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    msn = "hgeu8rhg"
    g_supply = site.insert_g_supply(
        sess,
        "87614362",
        "main",
        g_exit_zone,
        utc_datetime(2010, 1, 1),
        None,
        msn,
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
    )
    sess.commit()

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch(
        "chellow.reports.report_g_supplies_snapshot.open", return_value=mock_file
    )
    mocker.patch(
        "chellow.reports.report_g_supplies_snapshot.chellow.dloads.make_names",
        return_value=("a", "b"),
    )
    mocker.patch("chellow.reports.report_g_supplies_snapshot.os.rename")

    user = mocker.Mock()
    g_supply_id = g_supply.id
    date = utc_datetime(2020, 9, 1)

    chellow.reports.report_g_supplies_snapshot.content(date, g_supply_id, user)

    mock_file.seek(0)
    sheet = csv.reader(mock_file)
    table = list(sheet)

    expected = [
        [
            "Date",
            "Physical Site Id",
            "Physical Site Name",
            "Other Site Ids",
            "Other Site Names",
            "MPRN",
            "Exit Zone",
            "Meter Serial Number",
            "Correction Factor",
            "Unit",
            "Contract",
            "Account",
            "Supply Start",
            "Supply Finish",
        ],
        [
            "2020-09-01 01:00",
            "22488",
            "Water Works",
            "",
            "",
            "87614362",
            "EA1",
            "hgeu8rhg",
            "1",
            "M3",
            "Fusion 2020",
            "d7gthekrg",
            "2010-01-01 00:00",
            "",
        ],
    ]

    assert expected == table
