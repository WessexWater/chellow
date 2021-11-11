import csv
import threading
import traceback
from collections import deque
from datetime import datetime as Datetime, timedelta as Timedelta
from io import StringIO
from zipfile import ZipFile

from sqlalchemy import null, or_, select
from sqlalchemy.orm import joinedload

from werkzeug.exceptions import BadRequest

from chellow.models import (
    MarketRole,
    MeterPaymentType,
    MeterType,
    Mtc,
    Participant,
    Party,
    Pc,
    Session,
    Ssc,
    ValidMtcLlfcSscPc,
    VoltageLevel,
)
from chellow.utils import (
    ct_datetime,
    hh_format,
    to_ct,
    to_utc,
    utc_datetime_now,
)


process_id = 0
process_lock = threading.Lock()
processes = {}


def parse_date(date_str):
    if len(date_str) == 0:
        return None
    else:
        return to_utc(to_ct(Datetime.strptime(date_str, "%d/%m/%Y")))


def parse_to_date(date_str):
    if len(date_str) == 0:
        return None
    else:
        dt = to_ct(Datetime.strptime(date_str, "%d/%m/%Y"))
        dt += Timedelta(hours=23, minutes=30)
        return to_utc(dt)


def is_common_mtc(code):
    return 499 < code < 510 or 799 < code < 1000


VOLTAGE_MAP = {"24": {"602": {to_utc(ct_datetime(2010, 4, 1)): "LV"}}}


def _import_Line_Loss_Factor_Class(sess, csv_reader):
    VOLTAGE_LEVELS = dict(
        (v.code, v) for v in sess.execute(select(VoltageLevel)).scalars()
    )
    DNO_MAP = dict(
        (dno.participant.code, dno)
        for dno in sess.query(Party)
        .join(MarketRole)
        .filter(MarketRole.code == "R")
        .options(joinedload(Party.participant))
    )

    for values in csv_reader:
        participant_code = values[0]
        # market_role_code = values[1]
        llfc_code = values[3].zfill(3)
        valid_from = parse_date(values[4])
        description = values[5]
        is_import = values[6] in ("A", "B")
        is_substation = any(
            p in description for p in ("_SS", " SS", " S/S", "(S/S)", "sub", "Sub")
        )

        valid_to = parse_to_date(values[7])

        try:
            dno = DNO_MAP[participant_code]
        except KeyError:
            raise BadRequest(
                f"There is no DNO with participant code {participant_code}"
            )

        try:
            voltage_level_code = VOLTAGE_MAP[dno.dno_code][llfc_code][valid_from]
        except KeyError:
            voltage_level_code = "LV"
            description_upper = description.upper()
            for vl_code in VOLTAGE_LEVELS.keys():
                if vl_code in description_upper:
                    voltage_level_code = vl_code
                    break

        voltage_level = VOLTAGE_LEVELS[voltage_level_code]

        llfc = dno.find_llfc_by_code(sess, llfc_code, valid_from)

        if llfc is None:
            dno.insert_llfc(
                sess,
                llfc_code,
                description,
                voltage_level,
                is_substation,
                is_import,
                valid_from,
                valid_to,
            )

        else:
            llfc.description = description
            llfc.voltage_level = voltage_level
            llfc.is_substation = is_substation
            llfc.is_import = is_import
            llfc.valid_to = valid_to
            sess.flush()


def _import_Market_Participant(sess, csv_reader):
    for values in csv_reader:
        participant_code = values[0]
        participant_name = values[1]

        participant = Participant.find_by_code(sess, participant_code)

        if participant is None:
            Participant.insert(sess, participant_code, participant_name)

        else:
            participant.update(participant_name)
            sess.flush()


def _import_Market_Role(sess, csv_reader):
    for values in csv_reader:
        role_code = values[0]
        role_description = values[1]

        role = MarketRole.find_by_code(sess, role_code)

        if role is None:
            MarketRole.insert(sess, role_code, role_description)

        else:
            role.description = role_description
            sess.flush()


def _import_Market_Participant_Role(sess, csv_reader):
    for values in csv_reader:
        participant_code = values[0]
        participant = Participant.get_by_code(sess, participant_code)
        market_role_code = values[1]
        market_role = MarketRole.get_by_code(sess, market_role_code)
        valid_from = parse_date(values[2])
        party = Party.find_by_participant_role(
            sess, participant, market_role, valid_from
        )
        valid_to = parse_to_date(values[3])
        name = values[4]
        dno_code_str = values[14]
        dno_code = None if len(dno_code_str) == 0 else dno_code_str
        if dno_code == "99":
            continue

        if party is None:
            participant.insert_party(
                sess,
                market_role,
                name,
                valid_from,
                valid_to,
                dno_code,
            )

        else:
            party.name = name
            party.valid_to = valid_to
            party.dno_code = dno_code
            sess.flush()


def _import_Meter_Timeswitch_Class(sess, csv_reader):
    for values in csv_reader:
        code = values[0].zfill(3)
        valid_from = parse_date(values[1])
        valid_to = parse_to_date(values[2])
        description = values[3]
        is_common = values[4] == "T"

        if is_common:
            has_related_metering = values[5] == "T"
            meter_type_code = values[6]
            meter_type = MeterType.get_by_code(sess, meter_type_code, valid_from)
            meter_payment_type_code = values[7]
            meter_payment_type = MeterPaymentType.get_by_code(
                sess, meter_payment_type_code, valid_from
            )
            has_comms = values[8] == "T"
            is_hh = values[9] == "H"
            tpr_count_str = values[10]
            tpr_count = 0 if tpr_count_str == "" else int(tpr_count_str)

            mtc = Mtc.find_by_code(sess, None, code, valid_from)
            if mtc is None:
                Mtc.insert(
                    code,
                    description,
                    has_related_metering,
                    has_comms,
                    is_hh,
                    meter_type,
                    meter_payment_type,
                    tpr_count,
                    valid_from,
                    valid_to,
                )

            else:
                mtc.description = description
                mtc.has_related_metering = has_related_metering
                mtc.has_comms = has_comms
                mtc.is_hh = is_hh
                mtc.meter_type = meter_type
                mtc.meter_payment_type = meter_payment_type
                mtc.tpr_count = tpr_count
                mtc.valid_to = valid_to
                sess.flush()


def _import_MTC_in_PES_Area(sess, csv_reader):
    dnos = dict(
        (p.participant.code, p)
        for p in sess.query(Party)
        .join(Participant)
        .join(MarketRole)
        .filter(MarketRole.code == "R")
        .options(joinedload(Party.participant))
    )
    mtcs = dict(
        ((m.dno_id, m.code, m.valid_from), m)
        for m in sess.query(Mtc)
        .options(joinedload(Mtc.meter_type), joinedload(Mtc.meter_payment_type))
        .all()
    )
    meter_types = dict((m.code, m) for m in sess.execute(select(MeterType)).scalars())
    meter_payment_types = dict(
        (m.code, m) for m in sess.execute(select(MeterPaymentType)).scalars()
    )

    for values in csv_reader:
        code_str = values[0]
        if not Mtc.has_dno(code_str):
            continue

        code_int = int(code_str)
        code = code_str.zfill(3)
        participant_code = values[2]
        dno = dnos[participant_code]
        valid_from = parse_date(values[3])
        valid_to = parse_to_date(values[4])
        description = values[5]
        meter_type_code = values[6]
        meter_type = meter_types[meter_type_code]
        meter_payment_type_code = values[7]
        meter_payment_type = meter_payment_types[meter_payment_type_code]
        has_related_metering = code_int > 500
        has_comms = values[8] == "Y"
        is_hh = values[9] == "H"
        tpr_count_str = values[10]
        tpr_count = 0 if tpr_count_str == "" else int(tpr_count_str)

        mtc = mtcs.get((dno.id, code, valid_from))

        if mtc is None:
            Mtc.insert(
                sess,
                dno.dno_code,
                code,
                description,
                has_related_metering,
                has_comms,
                is_hh,
                meter_type,
                meter_payment_type,
                tpr_count,
                valid_from,
                valid_to,
            )

        else:
            mtc.description = description
            mtc.has_related_metering = has_related_metering
            mtc.has_comms = has_comms
            mtc.is_hh = is_hh
            mtc.meter_type = meter_type
            mtc.meter_payment_type = meter_payment_type
            mtc.tpr_count = tpr_count
            mtc.valid_to = valid_to
            sess.flush()


def _import_MTC_Meter_Type(sess, csv_reader):
    meter_types = dict(
        ((v.code, v.valid_from), v) for v in sess.execute(select(MeterType)).scalars()
    )
    for values in csv_reader:
        code = values[0]
        description = values[1]
        valid_from = parse_date(values[2])
        valid_to = parse_to_date(values[3])
        meter_type = meter_types.get((code, valid_from))

        if meter_type is None:
            MeterType.insert(sess, code, description, valid_from, valid_to)

        else:
            meter_type.description = description
            meter_type.valid_to = valid_to
            sess.flush()


def _import_Standard_Settlement_Configuration(sess, csv_reader):
    sscs = dict(
        ((v.code, v.valid_from), v) for v in sess.execute(select(Ssc)).scalars()
    )
    for values in csv_reader:
        code = values[0]
        valid_from = parse_date(values[1])
        valid_to = parse_to_date(values[2])
        description = values[3]
        is_import = values[4] == "I"
        ssc = sscs.get((code, valid_from))

        if ssc is None:
            Ssc.insert(sess, code, description, is_import, valid_from, valid_to)

        else:
            ssc.description = description
            ssc.is_import = is_import
            ssc.valid_to = valid_to
            sess.flush()


def _import_Valid_MTC_LLFC_SSC_PC_Combination(sess, csv_reader):
    dnos = {}
    mtcs = {}
    llfcs = {}
    sscs = {}
    pcs = dict((v.code, v) for v in sess.execute(select(Pc)).scalars())
    combos = dict(
        ((v.mtc.id, v.llfc.id, v.ssc.id, v.pc.id, v.valid_from), v)
        for v in sess.execute(select(ValidMtcLlfcSscPc)).scalars()
    )
    for values in csv_reader:
        mtc_code = values[0].zfill(3)  # Meter Timeswitch Class ID
        # Effective From Settlement Date (MTC)
        participant_code = values[2]  # Market Participant ID
        mtc_from_str = values[3]  # Effective From Settlement Date (MTCPA)
        mtc_from = parse_date(mtc_from_str)
        ssc_code = values[4]  # Standard Settlement Configuration ID
        ssc_from_str = values[5]  # Effective From Settlement date (VMTCSC)
        ssc_from = parse_date(ssc_from_str)
        llfc_code = values[6]  # Line Loss Factor Class ID
        llfc_from_str = values[7]  # Effective From Settlement Date (VMTCLSC)
        llfc_from = parse_date(llfc_from_str)
        pc_code = values[8].zfill(2)  # Profile Class ID
        valid_from_str = values[9]  # Effective From Settlement Date (VMTCLSPC)
        valid_from = parse_date(valid_from_str)
        valid_to_str = values[10]  # Effective To Settlement Date (VMTCLSPC)
        valid_to = parse_date(valid_to_str)
        # Preserved Tariff Indicator

        try:
            dno = dnos[(participant_code, valid_from)]
        except KeyError:
            dno = dnos[(participant_code, valid_from)] = sess.execute(
                select(Party)
                .join(Participant)
                .join(MarketRole)
                .where(
                    Participant.code == participant_code,
                    MarketRole.code == "R",
                    Party.valid_from <= valid_from,
                    or_(Party.valid_to == null(), Party.valid_to >= valid_from),
                )
            ).scalar_one()

        mtc_dno_id = dno.id if Mtc.has_dno(mtc_code) else None
        try:
            mtc = mtcs[(mtc_dno_id, mtc_code, mtc_from)]
        except KeyError:
            mtc = mtcs[(mtc_dno_id, mtc_code, mtc_from)] = Mtc.get_by_code(
                sess, dno, mtc_code, mtc_from
            )

        try:
            llfc = llfcs[(dno.id, llfc_code, llfc_from)]
        except KeyError:
            llfc = llfcs[(dno.id, llfc_code, llfc_from)] = dno.get_llfc_by_code(
                sess, llfc_code, llfc_from
            )

        try:
            ssc = sscs[(ssc_code, ssc_from)]
        except KeyError:
            ssc = sscs[(ssc_code, ssc_from)] = Ssc.get_by_code(sess, ssc_code, ssc_from)

        pc = pcs[pc_code]
        combo = combos.get((mtc.id, llfc.id, ssc.id, pc.id, valid_from))

        if combo is None:
            ValidMtcLlfcSscPc.insert(
                sess,
                mtc,
                llfc,
                ssc,
                pc,
                valid_from,
                valid_to,
            )

        else:
            combo.valid_to = valid_to
            sess.flush()


class MddImporter(threading.Thread):
    def __init__(self, f):
        threading.Thread.__init__(self)
        self.log_lines = deque(maxlen=1000)
        self.f = f
        self.rd_lock = threading.Lock()
        self.error_message = None

    def get_fields(self):
        return {"log": self.log_lines, "error_message": self.error_message}

    def run(self):
        def log_f(msg):
            self.log_lines.appendleft(f"{hh_format(utc_datetime_now())}: {msg}")

        sess = None
        try:
            sess = Session()
            zip_file = ZipFile(self.f)
            znames = {}

            for zname in zip_file.namelist():
                log_f(f"Inspecting {zname} in ZIP file")
                csv_file = StringIO(zip_file.read(zname).decode("utf-8"))
                csv_reader = iter(csv.reader(csv_file))
                next(csv_reader)  # Skip titles
                table_name = "_".join(zname.split("_")[:-1])
                znames[table_name] = csv_reader

            for tname, func in [
                ("Market_Participant", _import_Market_Participant),
                ("Market_Role", _import_Market_Role),
                ("Market_Participant_Role", _import_Market_Participant_Role),
                ("Line_Loss_Factor_Class", _import_Line_Loss_Factor_Class),
                ("Meter_Timeswitch_Class", _import_Meter_Timeswitch_Class),
                ("MTC_in_PES_Area", _import_MTC_in_PES_Area),
                ("MTC_Meter_Type", _import_MTC_Meter_Type),
                (
                    "Standard_Settlement_Configuration",
                    _import_Standard_Settlement_Configuration,
                ),
                (
                    "Valid_MTC_LLFC_SSC_PC_Combination",
                    _import_Valid_MTC_LLFC_SSC_PC_Combination,
                ),
            ]:

                if tname in znames:
                    log_f(f"Found {tname} and will now import it.")
                    func(sess, znames[tname])
                else:
                    log_f(f"Can't find {tname} in the ZIP file.")

            sess.commit()

        except BadRequest as e:
            sess.rollback()
            try:
                self.rd_lock.acquire()
                self.error_message = e.description
            finally:
                self.rd_lock.release()
        except BaseException:
            sess.rollback()
            try:
                self.rd_lock.acquire()
                self.error_message = traceback.format_exc()
            finally:
                self.rd_lock.release()
        finally:
            if sess is not None:
                sess.close()


def start_process(f):
    try:
        global process_id
        process_lock.acquire()
        proc_id = process_id
        process_id += 1
    finally:
        process_lock.release()

    process = MddImporter(f)
    processes[proc_id] = process
    process.start()
    return proc_id


def get_process_ids():
    try:
        process_lock.acquire()
        return processes.keys()
    finally:
        process_lock.release()


def get_process(pid):
    try:
        process_lock.acquire()
        return processes[pid]
    except KeyError:
        raise BadRequest(f"The importer with id {pid} can't be found.")
    finally:
        process_lock.release()
