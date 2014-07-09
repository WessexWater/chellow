from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql+pg8000://postgres:postgres@localhost:5432/chellow'
db = SQLAlchemy(app)


from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, or_, not_, and_, Enum
from sqlalchemy.orm import sessionmaker, relationship, backref, object_session
from sqlalchemy.orm.util import has_identity
from sqlalchemy import create_engine, ForeignKey, Sequence
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
import ast
import operator
import datetime
import pytz
import sys
import hashlib
import decimal

from sqlalchemy import Column, Integer, DateTime, Boolean, String, create_engine, ForeignKey, Sequence
from sqlalchemy.orm import relationship, backref, sessionmaker, _mapper_registry
from sqlalchemy.ext.declarative import declarative_base

app.logger.error("importing db module")
res = db.session.execute(
        """select count(*) from information_schema.tables """
        """where table_schema = 'public'""").fetchone()[0]
app.logger.error("res is " + str(res))

def set_read_write(sess):
    sess.execute("rollback")
    sess.execute("set transaction isolation level serializable read write")

class PersistentClass():
    @classmethod
    def get_by_id(cls, session, oid):
        obj = session.query(cls).get(oid)
        if obj is None:
            raise NotFoundException("There isn't a " + str(cls.__name__) +
                    " with the id " + str(oid))
        return obj

    id = Column(Integer, primary_key=True)

    def _eq_(self, other):
        if type(other) is type(self):
            return other.id == self.id
        else:
            return False


class VoltageLevel(db.Model, PersistentClass):

    __tablename__ = "voltage_level"
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    llfcs = relationship('Llfc', backref='voltage_level')

    @staticmethod
    def get_by_code(sess, code):
        vl = sess.query(VoltageLevel).filter_by(code=code).first()
        if vl is None:
            raise UserException("There is no voltage level with the code '"
                    + code + "'.")
        return vl


class GeneratorType(db.Model, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        gen_type = sess.query(GeneratorType).filter_by(code=code).first()
        if gen_type is None:
            raise UserException("There's no generator type with the code '"
                    + code + "'")
        return gen_type

Monad.getUtils()['imprt'](globals(), {
        'pre_db': ['PersistentClass', 'Base', 'VoltageLevel', 'GeneratorType', 'Session', 'Source', 'GspGroup', 'set_read_write'], 
        'utils': ['UserException', 'NotFoundException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH', 'parse_mpan_core', 'hh_format', 'CHANNEL_TYPES']})

class Source(db.Model, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        source = sess.query(Source).filter_by(code=code.strip()).first()
        if source is None:
            raise UserException("There's no source with the code '" +
                    code + "'")
        return source

    __tablename__ = "source"
    id = Column('id', Integer, Sequence('source_id_seq'), primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    supplies = relationship('Supply', backref='source')
    
class GspGroup(db.Model, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        group = sess.query(GspGroup).filter_by(code=code).first()
        if group is None:
            raise UserException("The GSP group with code " + code +
                        " can't be found.")
        return group

    __tablename__ = 'gsp_group'
    id = Column('id', Integer, Sequence('gsp_group_id_seq'), primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    supplies = relationship('Supply', backref='gsp_group')

class Site(db.Model, PersistentClass):
    __tablename__ = 'site'
    id = Column('id', Integer, Sequence('site_id_seq'), primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    site_eras = relationship('SiteEra', backref='site')
    snags = relationship('Snag', backref='site')

    def __init__(self, code, name):
        self.update(code, name)


class MarketRole(db.Model, PersistentClass):
    __tablename__ = 'market_role'
    id = Column(
        'id', Integer, Sequence('market_role_id_seq'), primary_key=True)
    code = Column(String(length=1), unique=True, nullable=False)
    description = Column(String, nullable=False, unique=True)
    contracts = relationship('Contract', backref='market_role')
    parties = relationship('Party', backref='market_role')

class Participant(db.Model, PersistentClass):
    __tablename__ = 'participant'
    id = Column('id', Integer, Sequence('participant_id_seq'), primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    parties = relationship('Party', backref='participant')

class Party(db.Model, PersistentClass):
    __tablename__ = 'party'
    id = Column('id', Integer, Sequence('party_id_seq'), primary_key=True)
    market_role_id = Column(Integer, ForeignKey('market_role.id'))
    participant_id = Column(Integer, ForeignKey('participant.id'))
    name = Column(String, nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime)
    users = relationship('User', backref='party')
    dno_code = Column(String)
    contracts = relationship('Contract', backref='party')
    mtcs = relationship('Mtc', backref='dno')
    llfcs = relationship('Llfc', backref='dno')

class Snag(db.Model, PersistentClass):
    __tablename__ = 'snag'
    id = Column('id', Integer, Sequence('snag_id_seq'), primary_key=True)
    site_id = Column(Integer, ForeignKey('site.id'))
    channel_id = Column(Integer, ForeignKey('channel.id'))
    date_created = Column(DateTime, nullable=False)
    is_ignored = Column(Boolean, nullable=False)
    description = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    finish_date = Column(DateTime, nullable=False)

    def __init__(self, site, channel, description, start_date, finish_date):
        if site is None and channel is None:
            raise UserException("The site and channel can't both be null.")
        if site is not None and channel is not None:
            raise UserException("The site and channel can't both be present.")
        self.site = site
        self.channel = channel

        self.date_created = datetime.datetime.now(pytz.utc)
        self.description = description
        self.is_ignored = False
        self.update(start_date, finish_date);

class ReadType(db.Model, PersistentClass):
    __tablename__ = 'read_type'
    id = Column('id', Integer, Sequence('read_type_id_seq'), primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)


class Cop(db.Model, PersistentClass):
    __tablename__ = 'cop'
    id = Column('id', Integer, Sequence('cop_id_seq'), primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    eras = relationship('Era', backref='cop')


class RegisterRead(db.Model, PersistentClass):
    __tablename__ = 'register_read'
    id = Column('id', Integer, Sequence('register_read_id_seq'),
            primary_key=True)
    bill_id = Column(Integer, ForeignKey('bill.id'), nullable=False)
    msn = Column(String, nullable=False)
    mpan_str = Column(String, nullable=False)
    coefficient = Column(Numeric, nullable=False)
    units = Column(String, nullable=False)
    tpr_id = Column(Integer, ForeignKey('tpr.id'))
    previous_date = Column(DateTime, nullable=False)
    previous_value = Column(Numeric, nullable=False)
    previous_type_id = Column(Integer, ForeignKey('read_type.id'))
    previous_type = relationship("ReadType",
                    primaryjoin="ReadType.id==RegisterRead.previous_type_id")
    present_date = Column(DateTime, nullable=False)
    present_value = Column(Numeric, nullable=False)
    present_type_id = Column(Integer, ForeignKey('read_type.id'))
    present_type = relationship("ReadType",
                    primaryjoin="ReadType.id==RegisterRead.present_type_id")

class Bill(db.Model, PersistentClass):

    __tablename__ = 'bill'
    id = Column('id', Integer, Sequence('bill_id_seq'), primary_key=True)
    batch_id = Column(Integer, ForeignKey('batch.id'), nullable=False)
    supply_id = Column(Integer, ForeignKey('supply.id'), nullable=False)
    issue_date = Column(DateTime, nullable=False)
    start_date = Column(DateTime, nullable=False)
    finish_date = Column(DateTime, nullable=False)
    net = Column(Numeric, nullable=False)
    vat = Column(Numeric, nullable=False)
    gross = Column(Numeric, nullable=False)
    account = Column(String, nullable=False)
    reference = Column(String, nullable=False)
    bill_type_id = Column(Integer, ForeignKey('bill_type.id'))
    breakdown = Column(String, nullable=False)
    kwh = Column(Numeric, nullable=False)
    reads = relationship('RegisterRead', backref='bill')

class BillType(db.Model, PersistentClass):
    __tablename__ = 'bill_type'
    id = Column('id', Integer, Sequence('bill_type_id_seq'), primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    bills = relationship('Bill', backref='bill_type')


class Pc(db.Model, PersistentClass):
    __tablename__ = 'pc'
    id = Column('id', Integer, Sequence('pc_id_seq'), primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    eras = relationship('Era', backref='pc')


class Batch(db.Model, PersistentClass):
    __tablename__ = 'batch'
    id = Column('id', Integer, Sequence('batch_id_seq'),
            primary_key=True)
    contract_id = Column(Integer, ForeignKey('contract.id'), nullable=False)
    reference = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False, unique=True)
    bills = relationship('Bill', backref='batch')

class Contract(db.Model, PersistentClass):
    __tablename__ = 'contract'
    id = Column('id', Integer, Sequence('contract_id_seq'), primary_key=True)
    is_core = Column(Boolean, nullable=False)
    name = Column(String, nullable=False)
    charge_script = Column(Text, nullable=False)
    properties = Column(Text, nullable=False)
    state = Column(Text, nullable=False)
    market_role_id = Column(Integer, ForeignKey('market_role.id'))
    __table_args__ = (UniqueConstraint('name', 'market_role_id'),)
    rate_scripts = relationship(
        "RateScript", back_populates="contract",
        primaryjoin="Contract.id==RateScript.contract_id")
    batches = relationship('Batch', backref='contract')
    supplies = relationship('Supply', backref='dno_contract')
    party_id = Column(Integer, ForeignKey('party.id'))

    start_rate_script_id = Column(Integer, ForeignKey('rate_script.id'))
    finish_rate_script_id = Column(Integer, ForeignKey('rate_script.id'))

    start_rate_script = relationship("RateScript",
            primaryjoin="RateScript.id==Contract.start_rate_script_id")
    finish_rate_script = relationship("RateScript",
            primaryjoin="RateScript.id==Contract.finish_rate_script_id")


class User(db.Model, PersistentClass):
    __tablename__ = 'user'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    email_address = Column(String, unique=True, nullable=False)
    password_digest = Column(String, nullable=False)
    user_role_id = Column(Integer, ForeignKey('user_role.id'))
    party_id = Column(Integer, ForeignKey('party.id'))


class UserRole(db.Model, PersistentClass):
    __tablename__ = 'user_role'
    id = Column('id', Integer, Sequence('user_role_id_seq'), primary_key=True)
    code = Column(String, unique=True, nullable=False)
    users = relationship('User', backref='user_role')

    def get_by_code(sess, code):
        role = sess.query(UserRole).filter_by(code=code.strip()).first()
        if role is None:
            raise UserException("There isn't a user role with code " + code + \
                    ".")
        return role


class RateScript(db.Model, PersistentClass):
    __tablename__ = "rate_script"
    id = Column('id', Integer, Sequence('rate_script_id_seq'),
            primary_key=True)
    contract_id = Column(Integer, ForeignKey('contract.id'))
    contract = relationship("Contract", back_populates="rate_scripts",
        primaryjoin="Contract.id==RateScript.contract_id")
    start_date = Column(DateTime, nullable=False)
    finish_date = Column(DateTime, nullable=True)
    script = Column(Text, nullable=False)

class Llfc(db.Model, PersistentClass):
    __tablename__ = 'llfc'
    id = Column('id', Integer, Sequence('llfc_id_seq'), primary_key=True)
    dno_id = Column(Integer, ForeignKey('party.id'))
    code = Column(String, nullable=False)
    description = Column(String)
    voltage_level_id = Column(Integer, ForeignKey('voltage_level.id'))
    is_substation = Column(Boolean, nullable=False)
    is_import = Column(Boolean, nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime)


class MeterType(db.Model, PersistentClass):
    __tablename__ = 'meter_type'
    id = Column('id', Integer, Sequence('meter_type_id_seq'), primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime)
    mtcs = relationship('Mtc', backref='meter_type')

class MeterPaymentType(db.Model, PersistentClass):
    __tablename__ = 'meter_payment_type'
    id = Column(
        'id', Integer, Sequence('meter_payment_type_id_seq'), primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    mtcs = relationship('Mtc', backref='meter_payment_type')


class Mtc(db.Model, PersistentClass):
    __tablename__ = 'mtc'
    id = Column('id', Integer, Sequence('mtc_id_seq'), primary_key=True)
    dno_id = Column(Integer, ForeignKey('party.id'))
    code = Column(String, nullable=False)
    description = Column(String, nullable=False)
    has_related_metering = Column(Boolean, nullable=False)
    has_comms = Column(Boolean, nullable=False)
    is_hh = Column(Boolean, nullable=False)
    meter_type_id = Column(Integer, ForeignKey('meter_type.id'))
    meter_payment_type_id = Column(Integer,
            ForeignKey('meter_payment_type.id'))
    tpr_count = Column(Integer)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime)
    eras = relationship('Era', backref='mtc')
    __table_args__ = (UniqueConstraint('dno_id', 'code'),)


class Tpr(db.Model, PersistentClass):
    __tablename__ = 'tpr'
    id = Column('id', Integer, Sequence('tpr_id_seq'), primary_key=True)
    code = Column(String, unique=True, nullable=False)
    is_teleswitch = Column(Boolean, nullable=False)
    is_gmt = Column(Boolean, nullable=False)
    clock_intervals = relationship('ClockInterval', backref='tpr')
    measurement_requirements = relationship(
        'MeasurementRequirement', backref='tpr')
    register_reads = relationship('RegisterRead', backref='tpr')

class ClockInterval(db.Model, PersistentClass):
    __tablename__ = 'clock_interval'
    id = Column(
        'id', Integer, Sequence('clock_interval_id_seq'), primary_key=True)
    tpr_id = Column(Integer, ForeignKey('tpr.id'))
    day_of_week = Column(Integer, nullable=False)
    start_day = Column(Integer, nullable=False)
    start_month = Column(Integer, nullable=False)
    end_day = Column(Integer, nullable=False)
    end_month = Column(Integer, nullable=False)
    start_hour = Column(Integer, nullable=False)
    start_minute = Column(Integer, nullable=False)
    end_hour = Column(Integer, nullable=False)
    end_minute = Column(Integer, nullable=False)

class MeasurementRequirement(db.Model, PersistentClass):
    __tablename__ = 'measurement_requirement'
    id = Column(
        'id', Integer, Sequence('measurement_requirement_id_seq'),
        primary_key=True)
    ssc_id = Column(Integer, ForeignKey('ssc.id'))
    tpr_id = Column(Integer, ForeignKey('tpr.id'))

class Ssc(db.Model, PersistentClass):
    __tablename__ = 'ssc'
    id = Column('id', Integer, Sequence('ssc_id_seq'), primary_key=True)
    code = Column(String, nullable=False)
    description = Column(String)
    is_import = Column(Boolean)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime)
    measurement_requirements = relationship(
        'MeasurementRequirement', backref='ssc')
    eras = relationship('Era', backref='ssc')


class SiteEra(db.Model, PersistentClass):
    __tablename__ = 'site_era'
    id = Column('id', Integer, Sequence('site_era_id_seq'), primary_key=True)
    site_id = Column(Integer, ForeignKey('site.id'))
    era_id = Column(Integer,
            ForeignKey('era.id'))
    is_physical = Column(Boolean, nullable=False)

class Era(db.Model, PersistentClass):
    __tablename__ = "era"
    id = Column('id', Integer, Sequence('era_id_seq'), primary_key=True)
    supply_id = Column(Integer, ForeignKey('supply.id'), nullable=False)
    site_eras = relationship('SiteEra', backref='era')
    start_date = Column(DateTime, nullable=False)
    finish_date = Column(DateTime)
    mop_contract_id = Column(
        Integer, ForeignKey('contract.id'), nullable=False)
    mop_contract = relationship(
        "Contract", primaryjoin="Contract.id==Era.mop_contract_id")
    mop_account = Column(String, nullable=False)
    hhdc_contract_id = Column(
        Integer, ForeignKey('contract.id'), nullable=False)
    hhdc_contract = relationship(
        "Contract", primaryjoin="Contract.id==Era.hhdc_contract_id")
    hhdc_account = Column(String)
    msn = Column(String)
    pc_id = Column(Integer, ForeignKey('pc.id'), nullable=False)
    mtc_id = Column(Integer, ForeignKey('mtc.id'), nullable=False)
    cop_id = Column(Integer, ForeignKey('cop.id'), nullable=False)
    ssc_id = Column(Integer, ForeignKey('ssc.id'))
    imp_mpan_core = Column(String)
    imp_llfc_id = Column(Integer, ForeignKey('llfc.id'))
    imp_llfc = relationship("Llfc", primaryjoin="Llfc.id==Era.imp_llfc_id")
    imp_supplier_contract_id = Column(Integer,
            ForeignKey('contract.id'))
    imp_supplier_contract = relationship("Contract",
            primaryjoin="Contract.id==Era.imp_supplier_contract_id")
    imp_supplier_account = Column(String)
    imp_sc = Column(Integer)
    exp_mpan_core = Column(String)
    exp_llfc_id = Column(Integer, ForeignKey('llfc.id'))
    exp_llfc = relationship("Llfc", primaryjoin="Llfc.id==Era.exp_llfc_id")
    exp_supplier_contract_id = Column(Integer, ForeignKey('contract.id'))
    exp_supplier_contract = relationship("Contract",
            primaryjoin="Contract.id==Era.exp_supplier_contract_id")
    exp_supplier_account = Column(String)
    exp_sc = Column(Integer)
    channels = relationship('Channel', backref='era')

class Channel(db.Model, PersistentClass):
    __tablename__ = 'channel'
    id = Column('id', Integer, Sequence('channel_id_seq'), primary_key=True)
    era_id = Column(Integer, ForeignKey('era.id'))
    imp_related = Column(Boolean, nullable=False)
    channel_type = Column(
        Enum('ACTIVE', 'REACTIVE_IMP', 'REACTIVE_EXP', name='channel_type'),
        nullable=False)
    hh_data = relationship('HhDatum', backref='channel')
    snag = relationship('Snag', backref='channel')

class Supply(db.Model, PersistentClass):
    __tablename__ = 'supply'
    id = Column('id', Integer, Sequence('supply_id_seq'), primary_key=True)
    name = Column(String, nullable=False)
    note = Column(Text, nullable=False)
    source_id = Column(Integer, ForeignKey('source.id'), nullable=False)
    generator_type_id = Column(Integer, ForeignKey('generator_type.id'))
    gsp_group_id = Column(Integer, ForeignKey('gsp_group.id'),
            nullable=False)
    dno_contract_id = Column(
        Integer, ForeignKey('contract.id'), nullable=False)
    eras = relationship('Era', backref='supply')
    bills = relationship('Bill', backref='supply')

class HhDatum(db.Model, PersistentClass):
    __tablename__ = 'hh_datum'
    id = Column('id', Integer, Sequence('hh_datum_id_seq'), 
        primary_key=True)
    channel_id = Column(Integer, ForeignKey('channel.id'))
    start_date = Column(DateTime, nullable=False)
    value = Column(Numeric, nullable=False)
    status = Column(String, nullable=False)
    last_modified = Column(DateTime, nullable=False)
    __table_args__ = (UniqueConstraint('channel_id', 'start_date'),)

class Report(db.Model, PersistentClass):
    __tablename__ = 'report'
    id = Column('id', Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    script = Column(Text, nullable=False)
    template = Column(Text, nullable=False)


def session():
    return Session()

if db.session.execute(
        """select count(*) from information_schema.tables """
        """where table_schema = 'public'""").fetchone()[0] == 0:
    app.logger.error("about to create all")
    db.create_all()
