from csv import writer
from io import BytesIO, StringIO
from zipfile import ZipFile

from sqlalchemy import select

import chellow.mdd_importer
from chellow.models import (
    MarketRole,
    MeterPaymentType,
    MeterType,
    Mtc,
    Participant,
    Party,
    Pc,
    Ssc,
    ValidMtcLlfcSscPc,
    VoltageLevel,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_import_Line_Loss_Factor_Class(sess):
    participant_code = "CALB"
    participant = Participant.insert(sess, participant_code, "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", to_utc(ct_datetime(2000, 1, 1)), None, "22"
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc_code = "004"
    llfc_description = "PC 5-8 & HH HV"
    dno.insert_llfc(
        sess,
        llfc_code,
        llfc_description,
        voltage_level,
        False,
        True,
        to_utc(ct_datetime(1996, 1, 1)),
        None,
    )
    sess.commit()

    row = [participant_code, "", "", llfc_code, "01/01/1996", llfc_description, "A", ""]

    csv_reader = iter([row])
    chellow.mdd_importer._import_Line_Loss_Factor_Class(sess, csv_reader)


def test_import_MTC_Meter_Type(sess):
    row = ["6A", "COP6(a)  20 days memory", "01/04/1996", ""]

    csv_reader = iter([row])
    chellow.mdd_importer._import_MTC_Meter_Type(sess, csv_reader)


def test_MddImporter(mocker, sess):
    participant_code = "ACCU"
    Participant.insert(sess, participant_code, "accu")
    market_role_code = "5"
    MarketRole.insert(sess, market_role_code, "mr5")
    sess.commit()

    party_name = "Callisto Data Limited"
    zf = BytesIO()
    vals = [
        [
            "Market Participant ID",
            "Market Participant Role Code",
            "Effective From Date (MPR)",
            "Effective To Date (MPR)",
            "Address 1",
            "Address 2",
            "Address 3",
            "Address 4",
            "Address 5",
            "Address 6",
            "Address 7",
            "Address 8",
            "Address 9",
            "Post Code",
            "Distributor Short Code",
        ],
        [
            participant_code,
            market_role_code,
            "18/12/2013",
            "",
            party_name,
            "11 Silver Fox Way",
            "Cobalt Business Park",
            "Newcastle Upon Tyne",
            "Tyne and Wear",
            "",
            "",
            "",
            "",
            "NE27 0QJ",
            "",
        ],
    ]

    csv_file = StringIO()
    csv_writer = writer(csv_file)
    for row in vals:
        csv_writer.writerow(row)

    with ZipFile(zf, "w") as f:
        f.writestr("Market_Participant_Role_316.csv", csv_file.getvalue())

    importer = chellow.mdd_importer.MddImporter(zf)
    importer.run()
    assert importer.error_message is None

    party = sess.execute(select(Party)).scalar_one()

    assert party.participant.code == participant_code
    assert party.market_role.code == market_role_code
    assert party.name == party_name
    assert party.valid_from == to_utc(ct_datetime(2013, 12, 18))
    assert party.valid_to is None
    assert party.dno_code is None


def test_parse_Valid_MTC_LLFC_SSC_PC_Combination(sess):
    participant_code = "EDFI"
    participant = Participant.insert(sess, participant_code, "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", to_utc(ct_datetime(2000, 1, 1)), None, "22"
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc_code = "906"
    llfc_description = "PC 5-8 & HH HV"
    llfc = dno.insert_llfc(
        sess,
        llfc_code,
        llfc_description,
        voltage_level,
        False,
        True,
        to_utc(ct_datetime(2009, 4, 16)),
        None,
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc = Mtc.insert(
        sess,
        dno,
        "001",
        "an mtc",
        False,
        False,
        True,
        meter_type,
        meter_payment_type,
        1,
        to_utc(ct_datetime(2009, 4, 16)),
        None,
    )
    ssc = Ssc.insert(
        sess, "0349", "an ssc", True, to_utc(ct_datetime(2009, 4, 16)), None
    )
    pc = Pc.insert(sess, "02", "dom", to_utc(ct_datetime(1996, 1, 1)), None)
    sess.commit()

    row = [
        "1",
        "01/04/1996",
        participant_code,
        "16/04/2009",
        "0349",
        "16/04/2009",
        "906",
        "16/04/2009",
        "2",
        "17/03/2010",
        "20/08/2014",
        "F",
    ]

    csv_reader = iter([row])
    chellow.mdd_importer._import_Valid_MTC_LLFC_SSC_PC_Combination(sess, csv_reader)
    sess.commit()
    ValidMtcLlfcSscPc.get_by_values(sess, mtc, llfc, ssc, pc, utc_datetime(2012, 1, 1))


def test_import_Market_Participant(sess):
    row = ["AAUL", "Alcan Aluminium Limited", ""]

    csv_reader = iter([row])
    chellow.mdd_importer._import_Market_Participant(sess, csv_reader)
