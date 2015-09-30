import shutil
import subprocess
import time
import sys
import chellow
from wsgiref.simple_server import make_server
import os.path
import requests
import signal
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Numeric, Enum,
    create_engine, ForeignKey, Sequence, UniqueConstraint)
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import pytz
from sqlalchemy.ext.declarative import declarative_base
import os
import hashlib
import pg8000
from chellow import app
pg8000.dbapi = pg8000


def log_message(msg):
    sys.stderr.write(msg + "\n")


def parse_hh_date(date_str):
    date_str = date_str.strip()
    if len(date_str) == 0:
        return None
    else:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M"). \
            replace(tzinfo=pytz.utc)


def read_file(pth, fname, attr):
    f = open(os.path.join(pth, fname), 'r')
    contents = f.read()
    f.close()
    if attr is None:
        return eval(contents)
    else:
        return {attr: contents}


def set_read_write(sess):
    sess.execute("set transaction isolation level serializable read write")

Base = declarative_base()


class UserException(Exception):
    pass


class Configuration(Base):
    __tablename__ = "configuration"
    id = Column('id', Integer, primary_key=True)
    properties = Column(Text, nullable=False)
    core_report_id = Column(Integer, nullable=False)
    user_report_id = Column(Integer, nullable=False)

    def __init__(self, properties):
        self.id = 0
        self.properties = properties
        self.core_report_id = 1
        self.user_report_id = 0

    def next_core_report_id(self):
        self.core_report_id += 2
        return self.core_report_id

    def next_user_report_id(self):
        self.user_report_id += 2
        return self.user_report_id


class VoltageLevel(Base):

    __tablename__ = "voltage_level"
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    llfcs = relationship('Llfc', backref='voltage_level')

    def __init__(self, code, name):
        self.code = code
        self.name = name


class Site(Base):
    __tablename__ = 'site'
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    site_eras = relationship('SiteEra', backref='site')
    snags = relationship('Snag', backref='site')

    def __init__(self, code, name):
        self.update(code, name)


class MarketRole(Base):
    __tablename__ = 'market_role'
    id = Column('id', Integer, primary_key=True)
    code = Column(String(length=1), unique=True, nullable=False)
    description = Column(String, nullable=False, unique=True)
    contracts = relationship('Contract', backref='market_role')
    parties = relationship('Party', backref='market_role')


class Participant(Base):
    __tablename__ = 'participant'
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    parties = relationship('Party', backref='participant')


class Party(Base):
    __tablename__ = 'party'
    id = Column('id', Integer, primary_key=True)
    market_role_id = Column(
        Integer, ForeignKey('market_role.id'), index=True)
    participant_id = Column(
        Integer, ForeignKey('participant.id'), index=True)
    name = Column(String, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    users = relationship('User', backref='party')
    dno_code = Column(String)
    contracts = relationship('Contract', backref='party')
    mtcs = relationship('Mtc', backref='dno')
    llfcs = relationship('Llfc', backref='dno')


class Source(Base):
    __tablename__ = "source"
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    supplies = relationship('Supply', backref='source')

    def __init__(self, code, name):
        self.code = code
        self.name = name


class GeneratorType(Base):
    __tablename__ = 'generator_type'
    id = Column(
        'id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    supplies = relationship('Supply', backref='generator_type')

    def __init__(self, code, description):
        self.code = code
        self.description = description


class GspGroup(Base):
    __tablename__ = 'gsp_group'
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    supplies = relationship('Supply', backref='gsp_group')


class Contract(Base):
    __tablename__ = 'contract'
    id = Column('id', Integer, primary_key=True)
    is_core = Column(Boolean, nullable=False)
    name = Column(String, nullable=False)
    charge_script = Column(Text, nullable=False)
    properties = Column(Text, nullable=False)
    state = Column(Text, nullable=False)
    market_role_id = Column(
        Integer, ForeignKey('market_role.id'), index=True)
    __table_args__ = (UniqueConstraint('name', 'market_role_id'),)
    rate_scripts = relationship(
        "RateScript", back_populates="contract",
        primaryjoin="Contract.id==RateScript.contract_id")
    batches = relationship('Batch', backref='contract')
    supplies = relationship('Supply', backref='dno_contract')
    party_id = Column(Integer, ForeignKey('party.id'), index=True)

    start_rate_script_id = Column(
        Integer, ForeignKey(
            'rate_script.id', use_alter=True,
            name='contract_start_rate_script_id_fkey'))
    finish_rate_script_id = Column(
        Integer, ForeignKey(
            'rate_script.id', use_alter=True,
            name='contract_finish_rate_script_id_fkey'))

    start_rate_script = relationship(
        "RateScript",
        primaryjoin="RateScript.id==Contract.start_rate_script_id")
    finish_rate_script = relationship(
        "RateScript",
        primaryjoin="RateScript.id==Contract.finish_rate_script_id")

    @staticmethod
    def get_non_core_by_name(sess, name):
        return Contract.get_by_role_code_name(sess, 'Z', name)

    @staticmethod
    def get_dno_by_id(sess, oid):
        return Contract.get_by_role_code_id(sess, 'R', oid)

    @staticmethod
    def get_dno_by_name(sess, name):
        cont = Contract.find_by_role_code_name(sess, 'R', name)
        if cont is None:
            raise UserException(
                "There isn't a DNO contract with the code '" + name + "'.")
        return cont

    @staticmethod
    def get_by_role_code_name(sess, role_code, name):
        cont = Contract.find_by_role_code_name(sess, role_code, name)
        if cont is None:
            raise UserException(
                "There isn't a contract with the role code '" + role_code +
                "' and name '" + name + "'.")
        return cont

    @staticmethod
    def find_by_role_code_name(sess, role_code, name):
        return sess.query(Contract).join(MarketRole).filter(
            MarketRole.code == role_code, Contract.name == name).first()

    @staticmethod
    def insert_non_core(
            is_core, name, charge_script, properties, start_date,
            finish_date, rate_script):
        return Contract.insert(
            is_core, name, Participant.get_by_code('CALB'), 'Z',
            charge_script, properties, start_date, finish_date,
            rate_script)

    @staticmethod
    def insert(
            session, is_core, name, participant, role_code, charge_script,
            properties, start_date, finish_date, rate_script):
        party = Party.get_by_participant_id_role_code(
            participant.id, role_code)
        contract = Contract(
            is_core, name, party, charge_script, properties)
        session.add(contract)
        session.flush()
        rscript = contract.insert_rate_script(start_date, rate_script)
        contract.update_rate_script(
            rscript, start_date, finish_date, rate_script)
        return contract


class RateScript(Base):
    __tablename__ = "rate_script"
    id = Column('id', Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey('contract.id'), index=True)
    contract = relationship(
        "Contract", back_populates="rate_scripts",
        primaryjoin="Contract.id==RateScript.contract_id")
    start_date = Column(
        DateTime(timezone=True), nullable=False, index=True)
    finish_date = Column(
        DateTime(timezone=True), nullable=True, index=True)
    script = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint('contract_id', 'start_date'),)


class Pc(Base):
    __tablename__ = 'pc'
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    eras = relationship('Era', backref='pc')


class MeterType(Base):
    __tablename__ = 'meter_type'
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    mtcs = relationship('Mtc', backref='meter_type')


class MeterPaymentType(Base):
    __tablename__ = 'meter_payment_type'
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    mtcs = relationship('Mtc', backref='meter_payment_type')


class Mtc(Base):
    __tablename__ = 'mtc'
    id = Column('id', Integer, primary_key=True)
    dno_id = Column(Integer, ForeignKey('party.id'))
    code = Column(String, nullable=False)
    description = Column(String, nullable=False)
    has_related_metering = Column(Boolean, nullable=False)
    has_comms = Column(Boolean, nullable=False)
    is_hh = Column(Boolean, nullable=False)
    meter_type_id = Column(Integer, ForeignKey('meter_type.id'))
    meter_payment_type_id = Column(
        Integer, ForeignKey('meter_payment_type.id'))
    tpr_count = Column(Integer)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime)
    eras = relationship('Era', backref='mtc')
    __table_args__ = (UniqueConstraint('dno_id', 'code'),)


class Supply(Base):
    __tablename__ = 'supply'
    id = Column('id', Integer, primary_key=True)
    name = Column(String, nullable=False)
    note = Column(Text, nullable=False)
    source_id = Column(Integer, ForeignKey('source.id'), nullable=False)
    generator_type_id = Column(Integer, ForeignKey('generator_type.id'))
    gsp_group_id = Column(
        Integer, ForeignKey('gsp_group.id'), nullable=False)
    dno_contract_id = Column(
        Integer, ForeignKey('contract.id'), nullable=False)
    eras = relationship('Era', backref='supply')
    bills = relationship('Bill', backref='supply')


class Cop(Base):
    __tablename__ = 'cop'
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    eras = relationship('Era', backref='cop')

    def __init__(self, code, description):
        self.code = code
        self.description = description


class Ssc(Base):
    __tablename__ = 'ssc'
    id = Column('id', Integer, primary_key=True)
    code = Column(String, nullable=False, index=True)
    description = Column(String)
    is_import = Column(Boolean, index=True)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime)
    measurement_requirements = relationship(
        'MeasurementRequirement', backref='ssc')
    eras = relationship('Era', backref='ssc')


class Llfc(Base):
    __tablename__ = 'llfc'
    id = Column('id', Integer, primary_key=True)
    dno_id = Column(Integer, ForeignKey('party.id'), index=True)
    code = Column(String, nullable=False)
    description = Column(String)
    voltage_level_id = Column(Integer, ForeignKey('voltage_level.id'))
    is_substation = Column(Boolean, nullable=False)
    is_import = Column(Boolean, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime)


class Era(Base):
    __tablename__ = "era"
    id = Column('id', Integer, primary_key=True)
    supply_id = Column(
        Integer, ForeignKey('supply.id'), nullable=False, index=True)
    site_eras = relationship('SiteEra', backref='era')
    start_date = Column(
        DateTime(timezone=True), nullable=False, index=True)
    finish_date = Column(DateTime(timezone=True), index=True)
    mop_contract_id = Column(
        Integer, ForeignKey('contract.id'), nullable=False, index=True)
    mop_contract = relationship(
        "Contract", primaryjoin="Contract.id==Era.mop_contract_id")
    mop_account = Column(String, nullable=False)
    hhdc_contract_id = Column(
        Integer, ForeignKey('contract.id'), nullable=False, index=True)
    hhdc_contract = relationship(
        "Contract", primaryjoin="Contract.id==Era.hhdc_contract_id")
    hhdc_account = Column(String)
    msn = Column(String)
    pc_id = Column(
        Integer, ForeignKey('pc.id'), nullable=False, index=True)
    mtc_id = Column(Integer, ForeignKey('mtc.id'), nullable=False)
    cop_id = Column(Integer, ForeignKey('cop.id'), nullable=False)
    ssc_id = Column(Integer, ForeignKey('ssc.id'))
    imp_mpan_core = Column(String)
    imp_llfc_id = Column(Integer, ForeignKey('llfc.id'))
    imp_llfc = relationship("Llfc", primaryjoin="Llfc.id==Era.imp_llfc_id")
    imp_supplier_contract_id = Column(
        Integer, ForeignKey('contract.id'), index=True)
    imp_supplier_contract = relationship(
        "Contract",
        primaryjoin="Contract.id==Era.imp_supplier_contract_id")
    imp_supplier_account = Column(String)
    imp_sc = Column(Integer)
    exp_mpan_core = Column(String)
    exp_llfc_id = Column(Integer, ForeignKey('llfc.id'))
    exp_llfc = relationship("Llfc", primaryjoin="Llfc.id==Era.exp_llfc_id")
    exp_supplier_contract_id = Column(Integer, ForeignKey('contract.id'))
    exp_supplier_contract = relationship(
        "Contract",
        primaryjoin="Contract.id==Era.exp_supplier_contract_id")
    exp_supplier_account = Column(String)
    exp_sc = Column(Integer)
    channels = relationship('Channel', backref='era')


class Channel(Base):
    __tablename__ = 'channel'
    id = Column('id', Integer, primary_key=True)
    era_id = Column(Integer, ForeignKey('era.id'), index=True)
    imp_related = Column(Boolean, nullable=False, index=True)
    channel_type = Column(
        Enum(
            'ACTIVE', 'REACTIVE_IMP', 'REACTIVE_EXP', name='channel_type'),
        nullable=False, index=True)
    hh_data = relationship('HhDatum', backref='channel')
    snag = relationship('Snag', backref='channel')
    __table_args__ = (
        UniqueConstraint('era_id', 'imp_related', 'channel_type'),)


class Snag(Base):
    __tablename__ = 'snag'
    id = Column('id', Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('site.id'), index=True)
    channel_id = Column(Integer, ForeignKey('channel.id'), index=True)
    date_created = Column(
        DateTime(timezone=True), nullable=False, index=True)
    is_ignored = Column(Boolean, nullable=False, index=True)
    description = Column(String, nullable=False, index=True)
    start_date = Column(
        DateTime(timezone=True), nullable=False, index=True)
    finish_date = Column(DateTime(timezone=True), index=True)


class ReadType(Base):
    __tablename__ = 'read_type'
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)

    def __init__(self, code, description):
        self.code = code
        self.description = description


class Batch(Base):
    __tablename__ = 'batch'
    id = Column('id', Integer, primary_key=True)
    contract_id = Column(
        Integer, ForeignKey('contract.id'), nullable=False, index=True)
    reference = Column(String, nullable=False)
    description = Column(String, nullable=False)
    bills = relationship('Bill', backref='batch')
    __table_args__ = (UniqueConstraint('contract_id', 'reference'), )


class BillType(Base):
    __tablename__ = 'bill_type'
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    bills = relationship('Bill', backref='bill_type')

    def __init__(self, code, description):
        self.code = code
        self.description = description


class Bill(Base):
    __tablename__ = 'bill'
    id = Column('id', Integer, primary_key=True)
    batch_id = Column(
        Integer, ForeignKey('batch.id'), nullable=False, index=True)
    supply_id = Column(
        Integer, ForeignKey('supply.id'), nullable=False, index=True)
    issue_date = Column(
        DateTime(timezone=True), nullable=False, index=True)
    start_date = Column(
        DateTime(timezone=True), nullable=False, index=True)
    finish_date = Column(
        DateTime(timezone=True), nullable=False, index=True)
    net = Column(Numeric, nullable=False)
    vat = Column(Numeric, nullable=False)
    gross = Column(Numeric, nullable=False)
    account = Column(String, nullable=False)
    reference = Column(String, nullable=False)
    bill_type_id = Column(Integer, ForeignKey('bill_type.id'), index=True)
    breakdown = Column(String, nullable=False)
    kwh = Column(Numeric, nullable=False)
    reads = relationship(
        'RegisterRead', backref='bill', cascade="all, delete-orphan",
        passive_deletes=True)


class Tpr(Base):
    __tablename__ = 'tpr'
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    is_teleswitch = Column(Boolean, nullable=False)
    is_gmt = Column(Boolean, nullable=False)
    clock_intervals = relationship('ClockInterval', backref='tpr')
    measurement_requirements = relationship(
        'MeasurementRequirement', backref='tpr')
    register_reads = relationship('RegisterRead', backref='tpr')


class RegisterRead(Base):
    __tablename__ = 'register_read'
    id = Column('id', Integer, primary_key=True)
    bill_id = Column(
        Integer, ForeignKey('bill.id', ondelete='CASCADE'), nullable=False,
        index=True)
    msn = Column(String, nullable=False, index=True)
    mpan_str = Column(String, nullable=False)
    coefficient = Column(Numeric, nullable=False)
    units = Column(Integer, nullable=False, index=True)
    tpr_id = Column(Integer, ForeignKey('tpr.id'), index=True)
    previous_date = Column(
        DateTime(timezone=True), nullable=False, index=True)
    previous_value = Column(Numeric, nullable=False)
    previous_type_id = Column(
        Integer, ForeignKey('read_type.id'), index=True)
    previous_type = relationship(
        "ReadType",
        primaryjoin="ReadType.id==RegisterRead.previous_type_id")
    present_date = Column(
        DateTime(timezone=True), nullable=False, index=True)
    present_value = Column(Numeric, nullable=False)
    present_type_id = Column(
        Integer, ForeignKey('read_type.id'), index=True)
    present_type = relationship(
        "ReadType",
        primaryjoin="ReadType.id==RegisterRead.present_type_id")


class UserRole(Base):
    __tablename__ = 'user_role'
    id = Column('id', Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    users = relationship('User', backref='user_role')

    def __init__(self, code):
        self.code = code


class User(Base):
    @staticmethod
    def insert(sess, email_address, password_digest, user_role, party):
        try:
            user = User(email_address, password_digest, user_role, party)
            sess.add(user)
            sess.flush()
        except Exception, e:
            if hasattr(e, 'orig') and \
                    e.orig.args[2] == 'duplicate key value violates ' + \
                    'unique constraint "user_email_address_key"':
                raise UserException(
                    "There's already a user with this email address.")
            else:
                raise e
        return user

    @staticmethod
    def digest(password):
        if sys.platform.startswith('java'):
            from net.sf.chellow.physical import User as JUser
            return JUser.digest(password)
        else:
            return hashlib.md5(password).hexdigest()

    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email_address = Column(String, unique=True, nullable=False)
    password_digest = Column(String, nullable=False)
    user_role_id = Column(Integer, ForeignKey('user_role.id'), index=True)
    party_id = Column(Integer, ForeignKey('party.id'))

    def __init__(self, email_address, password_digest, user_role, party):
        self.update(email_address, user_role, party)
        self.password_digest = password_digest

    def update(self, email_address, user_role, party):
        self.email_address = email_address
        self.user_role = user_role
        if user_role.code == 'party-viewer':
            if party is None:
                raise UserException(
                    "There must be a party if the role is party-viewer.")
            self.party = party
        else:
            self.party = None


class ClockInterval(Base):
    __tablename__ = 'clock_interval'
    id = Column(
        'id', Integer, primary_key=True)
    tpr_id = Column(Integer, ForeignKey('tpr.id'), index=True)
    day_of_week = Column(Integer, nullable=False)
    start_day = Column(Integer, nullable=False)
    start_month = Column(Integer, nullable=False)
    end_day = Column(Integer, nullable=False)
    end_month = Column(Integer, nullable=False)
    start_hour = Column(Integer, nullable=False)
    start_minute = Column(Integer, nullable=False)
    end_hour = Column(Integer, nullable=False)
    end_minute = Column(Integer, nullable=False)


class MeasurementRequirement(Base):
    __tablename__ = 'measurement_requirement'
    id = Column(
        'id', Integer, primary_key=True)
    ssc_id = Column(Integer, ForeignKey('ssc.id'), index=True)
    tpr_id = Column(Integer, ForeignKey('tpr.id'), index=True)


class SiteEra(Base):
    __tablename__ = 'site_era'
    id = Column('id', Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('site.id'), index=True)
    era_id = Column(Integer, ForeignKey('era.id'), index=True)
    is_physical = Column(Boolean, nullable=False, index=True)


class HhDatum(Base):
    __tablename__ = 'hh_datum'
    id = Column('id', Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('channel.id'), index=True)
    start_date = Column(
        DateTime(timezone=True), nullable=False, index=True)
    value = Column(Numeric, nullable=False)
    status = Column(String, nullable=False)
    last_modified = Column(
        DateTime(timezone=True), nullable=False, index=True)
    __table_args__ = (UniqueConstraint('channel_id', 'start_date'),)


class Report(Base):
    __tablename__ = 'report'
    id = Column('id', Integer, Sequence('report_id_seq'), primary_key=True)
    name = Column(String, unique=True, nullable=False)
    script = Column(Text, nullable=False)
    template = Column(Text)

    def __init__(self, session, id, is_core, name, script, template):
        configuration = session.query(Configuration).first()

        if id is None:
            if is_core:
                id = configuration.next_core_report_id()
            else:
                id = configuration.next_user_report_id()

        else:
            if is_core:
                if id > configuration.core_report_id:
                    configuration.core_report_id = id
            else:
                if id > configuration.user_report_id:
                    configuration.user_report_id(id)

        is_odd = id % 2 == 1
        if is_odd != is_core:
            raise UserException(
                "The ids of core reports must be odd, those of user "
                "reports"
                "must be even. Report id " + id + ", Is Odd? " + is_odd +
                ", is core? " + is_core + ".")
        self.id = id
        self.update(name, script, template)

    def update(self, name, script, template):
        self.name = name
        self.script = script
        if template is not None and len(template.strip()) == 0:
            template = None

        self.template = template


def chellow_test_setup():
    downloads_path = os.path.join(chellow.app.instance_path, 'downloads')
    if os.path.exists(downloads_path):
        shutil.rmtree(downloads_path)
    subprocess.Popen(["python", "test/ftp.py"])


def start_chellow():
    p = subprocess.Popen(["start_chellow_process"])

    instance_path = chellow.app.instance_path
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    with open(os.path.join(instance_path, 'pid'), "w") as pid_file:
        pid_file.write(str(p.pid))

    print "Testing if server is up..."
    status_code = None
    health_url = ''.join(
        [
            'http://localhost:', str(chellow.app.config['CHELLOW_PORT']),
            '/health'])
    while status_code != 200:
        try:

            print("Trying health URL " + health_url)
            r = requests.get(health_url)
            status_code = r.status_code
        except requests.exceptions.ConnectionError as e:
            print(e)
        time.sleep(1)


def start_chellow_process():
    webinf_path = os.path.join(chellow.app.root_path, 'web', 'WEB-INF')

    config = app.config
    db_name = config['PGDATABASE']
    first_email = config['CHELLOW_FIRST_EMAIL']
    first_password = config['CHELLOW_FIRST_PASSWORD']
    engine = create_engine(
        ''.join(
            [
                'postgresql+pg8000://',  config['PGUSER'], ':',
                config['PGPASSWORD'], '@', config['PGHOST'], ':',
                config['PGPORT'], '/', db_name]),
        isolation_level="SERIALIZABLE")

    Session = sessionmaker(bind=engine)
    session = Session()
    if engine.execute(
            """select count(*) from information_schema.tables """
            """where table_schema = 'public'""").scalar() == 0:
        log_message("Initializing database.")
        Base.metadata.create_all(engine)
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
            f = open(os.path.join(mdd_path, fname + '.csv'))
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
        configuration = Configuration('')
        session.add(configuration)
        session.commit()

        reports_path = os.path.join(webinf_path, 'reports')
        for report_id_str in os.listdir(reports_path):
            report_path = os.path.join(reports_path, report_id_str)
            params = {
                'session': session, 'id': int(report_id_str), 'is_core': True}
            set_read_write(session)
            for fname, attr in (
                    ('script.py', 'script'),
                    ('template.txt', 'template'),
                    ('meta.py', None)):
                params.update(read_file(report_path, fname, attr))
            session.add(Report(**params))
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
                params = {'market_role': market_role, 'name': contract_name}
                for fname, attr in (
                        ('charge_script.py', 'charge_script'),
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
        # Check the transaction isolation level is serializable
        isolation_level = session.execute(
            "show transaction isolation level").scalar()
        if isolation_level != 'serializable':
            raise Exception(
                "The transaction isolation level for database " + db_name +
                " should be 'serializable' but in fact " "it's " +
                isolation_level + ".")

        user_role = session.query(UserRole).filter(
            UserRole.code == 'editor').one()
        User.insert(
            session, first_email, User.digest(first_password), user_role, None)
        session.execute("create extension tablefunc")
        session.commit()
    else:
        sys.stderr.write("\nDatabase already initialized.")
    '''
    f = open(os.path.join(webinf_path, 'bootstrap.py'), 'rb')
    exec(f)
    ,
        {
            'webinf_path': webinf_path,
            'first_email': chellow.app.config['CHELLOW_FIRST_EMAIL'],
            'first_password': chellow.app.config['CHELLOW_FIRST_PASSWORD'],
            'user_name': chellow.app.config['PGUSER'],
            'password': chellow.app.config['PGPASSWORD'],
            'host_name': chellow.app.config['PGHOST'],
            'db_name': chellow.app.config['PGDATABASE']})
    '''
    startup_contract = Contract.get_non_core_by_name(session, 'startup')
    session.close()
    ns = {}
    exec(startup_contract.charge_script, ns)
    ns['on_start_up'](None)
    chellow_port = chellow.app.config['CHELLOW_PORT']
    httpd = make_server('', chellow_port, chellow.app)
    print "Serving HTTP on port " + str(chellow_port) + "..."

    # Respond to requests until process is killed
    httpd.serve_forever()


def stop_chellow():
    pid_path = os.path.join(chellow.app.instance_path, 'pid')
    if os.path.exists(pid_path):
        with open(pid_path, 'r') as pid_file:
            pid = int(pid_file.read().strip())

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as e:
            print(e)

        os.remove(pid_path)
