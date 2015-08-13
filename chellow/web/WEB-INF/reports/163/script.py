from net.sf.chellow.monad import Monad
import db
import templater
import utils
import sys
import StringIO
import csv
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Ssc, MeasurementRequirement = db.Ssc, db.MeasurementRequirement
Party, Llfc, VoltageLevel = db.Party, db.Llfc, db.VoltageLevel
Participant, MarketRole = db.Participant, db.MarketRole
render = templater.render
UserException = utils.UserException
inv, template = globals()['inv'], globals()['template']


def to_iso(dmy):
    if len(dmy) == 0:
        return ''
    else:
        return '-'.join([dmy[6:], dmy[3:5], dmy[:2]]) + ' 00:00'

method = inv.getRequest().getMethod()
if method == 'GET':
    render(inv, template, {})
elif method == 'POST':
    file_item = inv.getFileItem("file")
    file_name = file_item.getName()
    if not file_name.endswith('.csv'):
        raise UserException(
            "The file name should have the extension .csv.")
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
            VOLTAGE_LEVEL_CODES = set(
                [v.code for v in sess.query(VoltageLevel)])
            DNO_ID_MAP = dict((code, dno_id) for code, dno_id in sess.query(
                Participant.code,
                Party.id).join(Party).join(MarketRole).filter(
                MarketRole.code == 'R'))
            reader = iter(csv.reader(f))
            reader.next()
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
                        yield "# The participant code " + participant_code + \
                            " doesn't exist in Chellow.\n"
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

        finally:
            if sess is not None:
                sess.close()

    utils.send_response(inv, content, file_name='mdd.csv')
else:
    raise UserException("HTTP method not recognized.")
