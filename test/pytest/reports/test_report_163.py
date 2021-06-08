from csv import writer
from io import BytesIO, StringIO
from zipfile import ZipFile

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


def test_content(mocker, sess):
    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_163.open", return_value=mock_file)

    mocker.patch(
        "chellow.reports.report_163.chellow.dloads.make_names",
        return_value=("running.csv", "finished.csv"),
    )
    mocker.patch("chellow.reports.report_163.os.rename")

    mock_user = None

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
            "ACCU",
            "5",
            "18/12/2013",
            "",
            "Callisto Data Limited",
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
        f.writestr("Market_Participant_Role.txt", csv_file.getvalue())

    chellow.reports.report_163.content(zf, mock_user)

    assert (
        mock_file.getvalue()
        == "insert,party,5,ACCU,Callisto Data Limited,2013-12-18 00:00,,\n"
    )
