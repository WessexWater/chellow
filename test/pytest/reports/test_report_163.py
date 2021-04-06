import chellow.reports.report_163
from chellow.models import MarketRole, Participant, VoltageLevel, insert_voltage_levels
from chellow.utils import ct_datetime, to_utc


def test_parse_Line_Loss_Factor_Class(sess):
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
    chellow.reports.report_163._parse_Line_Loss_Factor_Class(sess, csv_reader)
