from net.sf.chellow.monad import Monad
import db
import templater
import utils
import sys
import StringIO
import csv
import os.path
import datetime
import pytz
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Ssc, MeasurementRequirement = db.Ssc, db.MeasurementRequirement
Party, Llfc, VoltageLevel = db.Party, db.Llfc, db.VoltageLevel
Participant, MarketRole = db.Participant, db.MarketRole
Mtc, Contract = db.Mtc, db.Contract
render = templater.render
UserException = utils.UserException
hh_format = utils.hh_format
inv, template = globals()['inv'], globals()['template']


def to_iso(dmy):
    if len(dmy) == 0:
        return ''
    else:
        return '-'.join([dmy[6:], dmy[3:5], dmy[:2]]) + ' 00:00'


def is_common_mtc(code):
    return 499 < code < 510 or 799 < code < 1000

method = inv.getRequest().getMethod()
if method == 'GET':
    render(inv, template, {})
elif method == 'POST':
    file_item = inv.getFileItem("file")
    file_path = file_item.getName()
    file_head, file_name = os.path.split(file_path)
    file_title, file_ext = os.path.splitext(file_name)
    if not file_ext == '.csv':
        raise UserException(
            "The file name should have the extension .csv, but in fact it "
            "has the extension '" + file_ext + "'.")
    idx = file_title.rfind('_')
    table = file_title[:idx]
    version = file_title[idx+1:]
    f = StringIO.StringIO()
    if sys.platform.startswith('java'):
        from java.io import InputStreamReader
        stream = InputStreamReader(file_item.getInputStream(), 'utf-8')
        bt = stream.read()
        while bt != -1:
            f.write(chr(bt))
            bt = stream.read()
    else:
        f.writelines(file_item.f.stream)

    f.seek(0)

    def content():
        sess = None
        try:
            sess = db.session()
            reader = iter(csv.reader(f))
            reader.next()
            if table == 'Line_Loss_Factor_Class':
                VOLTAGE_LEVEL_CODES = set(
                    [v.code for v in sess.query(VoltageLevel)])
                DNO_ID_MAP = dict(
                    (code, dno_id) for code, dno_id in sess.query(
                        Participant.code, Party.id).join(Party).join(
                        MarketRole).filter(MarketRole.code == 'R'))
                for i, values in enumerate(reader):
                    participant_code = values[0]
                    # market_role_code = values[1]
                    from_date_mpr = values[2]
                    llfc_code_raw = values[3]
                    # from_date_settlement = values[4]
                    llfc_description = values[5]
                    class_indicator = values[6]
                    to_date_settlement = values[7]

                    llfc_code = llfc_code_raw.zfill(3)
                    try:
                        llfc_id = sess.query(Llfc.id).filter(
                            Llfc.dno_id == DNO_ID_MAP[participant_code],
                            Llfc.code == llfc_code).first()
                    except KeyError:
                        llfc_id = None

                    if llfc_id is None:
                        participant = sess.query(Participant).filter(
                            Participant.code == participant_code).first()
                        if participant is None:
                            yield ''.join(
                                "# The participant code ", participant_code,
                                " doesn't exist in Chellow.\n")
                            continue

                        dno = Party.get_by_participant_code_role_code(
                            sess, participant.code, 'R')

                        voltage_level_code = 'LV'
                        llfc_description_upper = llfc_description.upper()
                        for vl_code in VOLTAGE_LEVEL_CODES:
                            if vl_code in llfc_description_upper:
                                voltage_level_code = vl_code
                                break

                        is_substation = False
                        for pattern in [
                                '_SS', ' SS', ' S/S',  '(S/S)', 'sub', 'Sub']:
                            if pattern in llfc_description:
                                is_substation = True
                                break

                        is_import = True
                        for pattern in ['C', 'D']:
                            if pattern in class_indicator:
                                is_import = False
                                break

                        yield ','.join(
                            (
                                '"' + str(v) + '"' for v in (
                                    'insert', 'llfc', dno.dno_code, llfc_code,
                                    llfc_description, voltage_level_code,
                                    is_substation, is_import,
                                    to_iso(from_date_mpr),
                                    to_iso(to_date_settlement)))) + "\n"
            elif table == 'Market_Participant':
                for i, values in enumerate(reader):
                    participant_code = values[0]
                    participant_name = values[1]

                    participant = sess.query(Participant).filter(
                        Participant.code == participant_code).first()

                    if participant is None:

                        yield ','.join(
                            (
                                '"' + str(v) + '"' for v in (
                                    'insert', 'participant', participant_code,
                                    participant_name))) + "\n"
                    elif participant_name != participant.name:
                        yield ','.join(
                            (
                                '"' + str(v) + '"' for v in (
                                    'update', 'participant', participant_code,
                                    participant_name))) + "\n"
            elif table == 'Market_Role':
                for i, values in enumerate(reader):
                    role_code = values[0]
                    role_description = values[1]

                    role = sess.query(MarketRole).filter(
                        MarketRole.code == role_code).first()

                    if role is None:
                        yield ','.join(
                            (
                                '"' + str(v) + '"' for v in (
                                    'insert', 'market_role', role_code,
                                    role_description))) + "\n"
                    elif role_description != role.description:
                        yield ','.join(
                            (
                                '"' + str(v) + '"' for v in (
                                    'update', 'market_role', participant_code,
                                    participant_name))) + "\n"
            elif table == 'Market_Participant_Role':
                for i, values in enumerate(reader):
                    participant_code = values[0]
                    market_role_code = values[1]
                    party = sess.query(Party).join(Participant). \
                        join(MarketRole).filter(
                            Participant.code == participant_code,
                            MarketRole.code == market_role_code).first()
                    valid_from_str = values[2]
                    valid_from = datetime.datetime.strptime(
                        valid_from_str, "%d/%m/%Y")
                    valid_to_str = values[3]
                    if valid_to_str == '':
                        valid_to = None
                    else:
                        valid_to = datetime.datetime.strptime(
                            valid_to_str, "%d/%m/%Y")
                    name = values[4]
                    dno_code = values[14]

                    if party is None:
                        yield ','.join(
                            (
                                '"' + str(v) + '"' for v in (
                                    'insert', 'party', market_role_code,
                                    participant_code, name,
                                    hh_format(valid_from),
                                    '' if valid_to is None else
                                    hh_format(valid_to), dno_code))) + "\n"
                    elif name != party.name or dno_code != party.dno_code:
                        yield ','.join(
                            (
                                '"' + str(v) + '"' for v in (
                                    'update', 'party', market_role_code,
                                    participant_code, name,
                                    hh_format(valid_from),
                                    '' if valid_to is None else
                                    hh_format(valid_to), dno_code))) + "\n"
            elif table == 'Meter_Timeswitch_Class':
                for i, values in enumerate(reader):
                    code_str = values[0]
                    code_int = int(code_str)
                    if is_common_mtc(code_int):
                        code = code_str.zfill(3)
                        valid_from_str = values[1]
                        valid_from = datetime.datetime.strptime(
                            valid_from_str, "%d/%m/%Y").replace(
                            tzinfo=pytz.utc)
                        valid_from_out = hh_format(valid_from)
                        valid_to_str = values[2]
                        if valid_to_str == '':
                            valid_to = None
                            valid_to_out = ''
                        else:
                            valid_to = datetime.datetime.strptime(
                                valid_to_str, "%d/%m/%Y").replace(
                                tzinfo=pytz.utc)
                            valid_to_out = hh_format(valid_to)
                        description = values[3]
                        # common_code_indicator = values[4]
                        has_related_metering_str = values[5]
                        has_related_metering = has_related_metering_str == 'T'
                        meter_type_code = values[6]
                        meter_payment_type_code = values[7]
                        has_comms_str = values[8]
                        has_comms = has_comms_str == 'T'
                        is_hh_str = values[9]
                        is_hh = is_hh_str == 'H'
                        tpr_count_str = values[10]
                        if tpr_count_str == '':
                            tpr_count = 0
                        else:
                            tpr_count = int(tpr_count_str)

                        mtc = Mtc.find_by_code(sess, None, code)
                        if mtc is None:
                            yield ','.join(
                                (
                                    '"' + str(v) + '"' for v in (
                                        'insert', 'mtc', '', code,
                                        description, has_related_metering,
                                        has_comms, is_hh, meter_type_code,
                                        meter_payment_type_code, tpr_count,
                                        valid_from_out, valid_to_out))) + "\n"
                        elif (
                                description, has_related_metering, has_comms,
                                is_hh, meter_type_code,
                                meter_payment_type_code, tpr_count, valid_from,
                                valid_to) != (
                                mtc.description, mtc.has_related_metering,
                                mtc.has_comms, mtc.is_hh, mtc.meter_type.code,
                                mtc.meter_payment_type.code, mtc.tpr_count,
                                mtc.valid_from, mtc.valid_to):
                            yield ','.join(
                                (
                                    '"' + str(v) + '"' for v in (
                                        'update', 'mtc', '', code,
                                        description, has_related_metering,
                                        has_comms, is_hh, meter_type_code,
                                        meter_payment_type_code, tpr_count,
                                        valid_from_out, valid_to_out))) + "\n"
            elif table == 'MTC_in_PES_Area':
                for i, values in enumerate(reader):
                    code_str = values[0]
                    code_int = int(code_str)
                    if not is_common_mtc(code_int):
                        code = code_str.zfill(3)
                        participant_code = values[2]
                        dno = Party.get_by_participant_code_role_code(
                            sess, participant_code, 'R')
                        valid_from_str = values[3]
                        valid_from = datetime.datetime.strptime(
                            valid_from_str, "%d/%m/%Y").replace(
                            tzinfo=pytz.utc)
                        valid_from_out = hh_format(valid_from)
                        valid_to_str = values[4]
                        if valid_to_str == '':
                            valid_to = None
                            valid_to_out = ''
                        else:
                            valid_to = datetime.datetime.strptime(
                                valid_to_str, "%d/%m/%Y").replace(
                                tzinfo=pytz.utc)
                            valid_to_out = hh_format(valid_to)
                        description = values[5]
                        meter_type_code = values[6]
                        meter_payment_type_code = values[7]
                        has_related_metering = code_int > 500
                        has_comms = values[8] == 'Y'
                        is_hh = values[9] == 'H'
                        tpr_count_str = values[10]
                        if tpr_count_str == '':
                            tpr_count = 0
                        else:
                            tpr_count = int(tpr_count_str)

                        mtc = Mtc.find_by_code(sess, dno, code)
                        if mtc is None:
                            yield ','.join(
                                (
                                    '"' + str(v) + '"' for v in (
                                        'insert', 'mtc', dno.dno_code, code,
                                        description, has_related_metering,
                                        has_comms, is_hh, meter_type_code,
                                        meter_payment_type_code, tpr_count,
                                        valid_from_out, valid_to_out))) + "\n"
                        elif (
                                description, has_related_metering, has_comms,
                                is_hh, meter_type_code,
                                meter_payment_type_code, tpr_count, valid_from,
                                valid_to) != (
                                mtc.description, mtc.has_related_metering,
                                mtc.has_comms, mtc.is_hh, mtc.meter_type.code,
                                mtc.meter_payment_type.code, mtc.tpr_count,
                                mtc.valid_from, mtc.valid_to):
                            yield ','.join(
                                (
                                    '"' + str(v) + '"' for v in (
                                        'update', 'mtc', dno.dno_code, code,
                                        description, has_related_metering,
                                        has_comms, is_hh, meter_type_code,
                                        meter_payment_type_code, tpr_count,
                                        valid_from_out, valid_to_out))) + "\n"
            else:
                raise Exception("The table " + table + " is not recognized.")

        finally:
            if sess is not None:
                sess.close()

    utils.send_response(inv, content, file_name=table + '_' + version + '.csv')
else:
    raise UserException("HTTP method not recognized.")
