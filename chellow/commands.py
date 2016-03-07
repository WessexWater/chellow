import shutil
import subprocess
import sys
import chellow
import os.path
import datetime
import pytz
import os
from chellow import app
import chellow.rcrc
import chellow.bsuos
import chellow.system_price
import chellow.hh_importer
import chellow.tlms
import chellow.bank_holidays
import chellow.dloads
from chellow.models import (
    db, set_read_write, VoltageLevel, UserRole, Source, GeneratorType,
    ReadType, Cop, BillType, Report, MarketRole, Party, Participant, Contract,
    RateScript)
from daemon import runner
import waitress


def log_message(msg):
    sys.stderr.write(str(msg) + "\n")


def read_file(pth, fname, attr):
    with open(os.path.join(pth, fname), 'r') as f:
        contents = f.read()
    if attr is None:
        return eval(contents)
    else:
        return {attr: contents}


def chellow_db_init():
    session = chellow.models.Session()
    webinf_path = chellow.app.root_path
    config = app.config
    db_name = config['PGDATABASE']
    if find_db_version(session) is None:
        log_message("Initializing database.")
        db.create_all()
        set_read_write(session)
        for code, desc in (
                ("LV", "Low voltage"),
                ("HV", "High voltage"),
                ("EHV", "Extra high voltage")):
            session.add(VoltageLevel(code, desc))
        session.commit()

        set_read_write(session)
        for code in ("editor", "viewer", "party-viewer"):
            session.add(UserRole(code))
        session.commit()

        set_read_write(session)
        for code, desc in (
                ('net', "Public distribution system."),
                ('sub', "Sub meter"),
                ('gen-net', "Generator connected directly to network."),
                ('gen', "Generator."),
                ('3rd-party', "Third party supply."),
                (
                    '3rd-party-reverse',
                    "Third party supply with import going out of the site."),
                ):
            session.add(Source(code, desc))
        session.commit()

        set_read_write(session)
        for code, desc in (
                ("chp", "Combined heat and power."),
                ("lm", "Load management."),
                ("turb", "Water turbine."),
                ("pv", "Solar Photovoltaics.")):
            session.add(GeneratorType(code, desc))
        session.commit()

        set_read_write(session)
        for code, desc in (
                ("N", "Normal"),
                ("N3", "Normal 3rd Party"),
                ("C", "Customer"),
                ("E", "Estimated"),
                ("E3", "Estimated 3rd Party"),
                ("EM", "Estimated Manual"),
                ("W", "Withdrawn"),
                ("X", "Exchange"),
                ("CP", "Computer"),
                ("IF", "Information")):
            session.add(ReadType(code, desc))
        session.commit()

        set_read_write(session)
        for code, desc in (
                ('1', "CoP 1"),
                ('2', "CoP 2"),
                ('3', "CoP 3"),
                ('4', "CoP 4"),
                ('5', "CoP 5"),
                ('6a', "CoP 6a 20 day memory"),
                ('6b', "CoP 6b 100 day memory"),
                ('6c', "CoP 6c 250 day memory"),
                ('6d', "CoP 6d 450 day memory"),
                ('7', "CoP 7")):
            session.add(Cop(code, desc))
        session.commit()

        set_read_write(session)
        for code, desc in (
                ("F", "Final"),
                ("N", "Normal"),
                ("W", "Withdrawn")):
            session.add(BillType(code, desc))
        session.commit()

        dbapi_conn = session.connection().connection.connection
        cursor = dbapi_conn.cursor()
        mdd_path = os.path.join(webinf_path, 'mdd')
        for tname, fname in (
                ("gsp_group", "GSP_Group"),
                ("pc", "Profile_Class"),
                ("market_role", "Market_Role"),
                ("participant", "Market_Participant"),
                ("party", "Market_Participant_Role"),
                ("llfc", "Line_Loss_Factor_Class"),
                ("meter_type", "MTC_Meter_Type"),
                ("meter_payment_type", "MTC_Payment_Type"),
                ("mtc", "Meter_Timeswitch_Class"),
                ("tpr", "Time_Pattern_Regime"),
                ("clock_interval", "Clock_Interval"),
                ("ssc", "Standard_Settlement_Configuration"),
                ("measurement_requirement", "Measurement_Requirement")):
            f = open(os.path.join(mdd_path, fname + '.csv'), 'rb')
            cursor.execute(
                "set transaction isolation level serializable read write")
            if tname == 'llfc':
                cursor.execute(
                    "COPY " + tname +
                    " (dno_id, code, description, voltage_level_id, "
                    "is_substation, is_import, valid_from, valid_to) "
                    "FROM STDIN CSV HEADER", stream=f)
            elif tname == 'participant':
                cursor.execute(
                    "COPY " + tname + " (code, name) "
                    "FROM STDIN CSV HEADER", stream=f)
            elif tname == 'market_role':
                cursor.execute(
                    "COPY " + tname + " (code, description) "
                    "FROM STDIN CSV HEADER", stream=f)
            elif tname == 'party':
                cursor.execute(
                    "COPY " + tname + " (market_role_id, participant_id, "
                    "name, valid_from, valid_to, dno_code) "
                    "FROM STDIN CSV HEADER", stream=f)
            elif tname == 'meter_type':
                cursor.execute(
                    "COPY " + tname + " (code, description, valid_from, "
                    "valid_to) FROM STDIN CSV HEADER", stream=f)
            elif tname == 'mtc':
                cursor.execute(
                    "COPY " + tname + " (dno_id, code, description, "
                    "has_related_metering, has_comms, is_hh, meter_type_id, "
                    "meter_payment_type_id, tpr_count, valid_from, valid_to) "
                    "FROM STDIN CSV HEADER", stream=f)
            else:
                cursor.execute(
                    "COPY " + tname + " FROM STDIN CSV HEADER", stream=f)
            dbapi_conn.commit()
            f.close()

        set_read_write(session)
        for path_name, role_code in (
                ('non_core_contracts', 'Z'),
                ('dno_contracts', 'R')):
            contracts_path = os.path.join(webinf_path, path_name)

            for contract_name in sorted(os.listdir(contracts_path)):
                contract_path = os.path.join(contracts_path, contract_name)
                params = {'name': contract_name, 'charge_script': ''}
                for fname, attr in (
                        ('meta.py', None),
                        ('properties.py', 'properties'),
                        ('state.py', 'state')):
                    params.update(read_file(contract_path, fname, attr))
                params['party'] = session.query(Party).join(Participant). \
                    join(MarketRole). \
                    filter(
                        Participant.code == params['participant_code'],
                        MarketRole.code == role_code).one()
                del params['participant_code']
                contract = Contract(**params)
                session.add(contract)

                session.flush()
                rscripts_path = os.path.join(contract_path, 'rate_scripts')
                for rscript_fname in sorted(os.listdir(rscripts_path)):
                    if not rscript_fname.endswith('.py'):
                        continue
                    try:
                        start_str, finish_str = \
                            rscript_fname.split('.')[0].split('_')
                    except ValueError:
                        raise Exception(
                            "The rate script " + rscript_fname +
                            " in the directory " + rscripts_path +
                            " should consist of two dates separated by an " +
                            "underscore.")
                    start_date = datetime.datetime.strptime(
                        start_str, "%Y%m%d%H%M").replace(tzinfo=pytz.utc)
                    if finish_str == 'ongoing':
                        finish_date = None
                    else:
                        finish_date = datetime.datetime.strptime(
                            finish_str, "%Y%m%d%H%M").replace(tzinfo=pytz.utc)
                    rparams = {
                        'start_date': start_date,
                        'finish_date': finish_date,
                        'contract': contract}
                    rparams.update(
                        read_file(rscripts_path, rscript_fname, 'script'))
                    session.add(RateScript(**rparams))
                    session.flush()

                session.flush()
                # Assign start and finish rate scripts
                scripts = session.query(RateScript). \
                    filter(RateScript.contract_id == contract.id). \
                    order_by(RateScript.start_date).all()
                contract.start_rate_script = scripts[0]
                contract.finish_rate_script = scripts[-1]
        session.commit()

        set_read_write(session)
        session.execute(
            "alter database " + db_name +
            " set default_transaction_isolation = 'serializable'")
        session.execute(
            "alter database " + db_name +
            " set default_transaction_deferrable = on")
        session.execute(
            "alter database " + db_name + " SET DateStyle TO 'ISO, YMD'")
        session.execute(
            "alter database " + db_name +
            " set default_transaction_read_only = on")
        session.commit()
        session.close()
        chellow.models.db.engine.dispose()
        session = chellow.models.Session()
        # Check the transaction isolation level is serializable
        isolation_level = session.execute(
            "show transaction isolation level").scalar()
        if isolation_level != 'serializable':
            raise Exception(
                "The transaction isolation level for database " + db_name +
                " should be 'serializable' but in fact " "it's " +
                isolation_level + ".")

        set_read_write(session)
        session.execute("create extension tablefunc")
        conf = session.query(Contract).join(MarketRole).filter(
            Contract.name == 'configuration', MarketRole.code == 'Z').one()
        state = conf.make_state()
        state['db_version'] = len(upgrade_funcs)
        conf.update_state(state)
        session.commit()
    else:
        log_message("It seems that the database is already initialized.")


def chellow_test_setup():
    downloads_path = os.path.join(chellow.app.instance_path, 'downloads')
    if os.path.exists(downloads_path):
        shutil.rmtree(downloads_path)
    subprocess.Popen(["python", "test/ftp.py"])


def db_upgrade_0_to_1(session):
    webinf_path = chellow.app.root_path
    reports_path = os.path.join(webinf_path, 'reports')
    for report_id_str in os.listdir(reports_path):
        report_path = os.path.join(reports_path, report_id_str)
        report_id = str(report_id_str)
        report = session.query(Report).filter(Report.id == report_id).first()
        if report is None:
            continue
        report.script = read_file(report_path, 'script.py', 'script')['script']
        session.commit()

    set_read_write(session)
    for path_name, role_code in (
            ('non_core_contracts', 'Z'),
            ('dno_contracts', 'R')):
        contracts_path = os.path.join(webinf_path, path_name)
        market_role = session.query(MarketRole). \
            filter(MarketRole.code == role_code).one()

        for contract_name in sorted(os.listdir(contracts_path)):
            contract_path = os.path.join(contracts_path, contract_name)
            charge_script = read_file(
                contract_path, 'charge_script.py',
                'charge_script')['charge_script']
            contract = session.query(Contract).filter(
                Contract.name == contract_name,
                Contract.market_role == market_role).first()
            if contract is None:
                print("missing", contract_name)
                continue
            contract.charge_script = charge_script
            session.add(contract)

upgrade_funcs = [db_upgrade_0_to_1]


def chellow_db_upgrade():
    session = chellow.models.Session()
    set_read_write(session)
    db_version = find_db_version(session)
    curr_version = len(upgrade_funcs)
    if db_version is None:
        log_message(
            "It looks like the chellow database hasn't been initialized. "
            "To initialize the database run the 'chellow_db_init' command.")
        exit(1)
    elif db_version == curr_version:
        log_message(
            "The database version is " + str(db_version) +
            " and the latest version is " + str(curr_version) +
            " so it doesn't look like you need to run an upgrade.")
        exit(1)
    elif db_version > curr_version:
        log_message(
            "The database version is " + str(db_version) +
            " and the latest database version is " + str(curr_version) +
            " so it looks like you're using an old version of Chellow.")
        exit(1)

    log_message(
        "Upgrading from database version " + str(db_version) +
        " to database version " + str(db_version + 1) + ".")
    upgrade_funcs[db_version](session)
    conf = session.query(Contract).join(MarketRole).filter(
        Contract.name == 'configuration', MarketRole.code == 'Z').one()
    state = conf.make_state()
    state['db_version'] = db_version + 1
    conf.update_state(state)
    session.commit()
    session.close()
    log_message(
        "Successfully upgraded from database version " + str(db_version) +
        " to database version " + str(db_version + 1) + ".")


def find_db_version(session):
    engine = session.get_bind()
    if engine.execute(
            """select count(*) from information_schema.tables """
            """where table_schema = 'public'""").scalar() == 0:
        return None
    conf = session.query(Contract).join(MarketRole).filter(
        Contract.name == 'configuration', MarketRole.code == 'Z').one()
    conf_state = conf.make_state()
    return conf_state.get('db_version', 0)


def is_db_version_correct(session):
    db_version = find_db_version(session)
    curr_version = len(upgrade_funcs)
    if db_version is None:
        log_message(
            "It looks like the chellow database hasn't been initialized. "
            "To initialize the database run the 'chellow_db_init' command.")
    elif db_version < curr_version:
        log_message(
            "It looks like the version of the Chellow database is " +
            str(db_version) + " but this version of Chellow needs version " +
            str(curr_version) + ". To upgrade the database run the " +
            "'chellow_db_upgrade' command.")
    else:
        return True
    return False


class ChellowD():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = os.path.join(
            chellow.app.instance_path, 'chellow.pid')
        self.pidfile_timeout = 5

    def run(self):
        chellow_port = chellow.app.config['CHELLOW_PORT']
        waitress.serve(chellow.app, host='0.0.0.0', port=chellow_port)


def chellow_command():
    chellowd = ChellowD()
    daemon_runner = runner.DaemonRunner(chellowd)
    daemon_runner.do_action()
