import datetime
import math
import operator
import os.path
import sys
import traceback
from ast import literal_eval, parse
from binascii import hexlify, unhexlify
from collections.abc import Mapping, Set
from datetime import datetime as Datetime
from decimal import Decimal
from hashlib import pbkdf2_hmac
from itertools import takewhile

from dateutil.relativedelta import relativedelta

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    and_,
    create_engine,
    delete,
    event,
    not_,
    null,
    or_,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.exc import (
    IntegrityError,
    NoResultFound,
    ProgrammingError,
    SQLAlchemyError,
)
from sqlalchemy.orm import (
    aliased,
    attributes,
    declarative_base,
    joinedload,
    relationship,
    sessionmaker,
)
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql.expression import false, true

from werkzeug.exceptions import BadRequest, NotFound

from zish import dumps, loads

from chellow.utils import (
    HH,
    c_months_u,
    ct_datetime,
    ct_datetime_now,
    hh_after,
    hh_before,
    hh_format,
    hh_max,
    hh_min,
    hh_range,
    next_hh,
    parse_mpan_core,
    prev_hh,
    to_utc,
    utc_datetime,
    utc_datetime_now,
)


config = {
    "PGUSER": "postgres",
    "PGPASSWORD": "postgres",
    "PGHOST": "localhost",
    "PGDATABASE": "chellow",
    "PGPORT": "5432",
}


if "RDS_HOSTNAME" in os.environ:
    for conf_name, rds_name in (
        ("PGDATABASE", "RDS_DB_NAME"),
        ("PGUSER", "RDS_USERNAME"),
        ("PGPASSWORD", "RDS_PASSWORD"),
        ("PGHOST", "RDS_HOSTNAME"),
        ("PGPORT", "RDS_PORT"),
    ):
        config[conf_name] = os.environ[rds_name]

for var_name in (
    "PGUSER",
    "PGPASSWORD",
    "PGHOST",
    "PGPORT",
    "PGDATABASE",
    "CHELLOW_PORT",
):
    if var_name in os.environ:
        config[var_name] = os.environ[var_name]

db_url = "".join(
    [
        "postgresql+pg8000://",
        config["PGUSER"],
        ":",
        config["PGPASSWORD"],
        "@",
        config["PGHOST"],
        ":",
        config["PGPORT"],
        "/",
        config["PGDATABASE"],
    ]
)

Base = declarative_base()

engine = None
session = None

rengine = None
rsession = None


def start_sqlalchemy():
    global engine, session, rengine, rsession

    if engine is not None or session is not None:
        raise Exception("SQLAlchemy has already been started!")

    engine = create_engine(
        db_url, execution_options={"isolation_level": "SERIALIZABLE"}
    )
    session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    rengine = engine.execution_options(
        isolation_level="SERIALIZABLE",
        postgresql_readonly=True,
        postgresql_deferrable=True,
    )
    rsession = sessionmaker(bind=rengine)


def stop_sqlalchemy():
    global engine, session, rengine, rsession

    if engine is not None:
        engine.dispose()
        engine = None
        session = None
        rengine = None
        rsession = None


def Session():
    return session()


def RSession():
    return rsession()


CHANNEL_TYPES = ("ACTIVE", "REACTIVE_IMP", "REACTIVE_EXP")


def log_message(msg):
    sys.stderr.write(str(msg) + "\n")


@event.listens_for(Engine, "handle_error")
def handle_exception(context):
    msg = "could not serialize access due to read/write dependencies among transactions"
    exc_txt = str(context.original_exception)
    if msg in exc_txt:
        raise BadRequest(
            f"Temporary conflict with other database writes. Might work if you "
            f"try again. {exc_txt}"
        )
    elif "out of shared memory" in exc_txt:
        traces = []
        for thread_id, stack in sys._current_frames().items():
            traces.append(f"\n# ThreadID: {thread_id}")
            for filename, lineno, name, line in traceback.extract_stack(stack):
                traces.append(f'File: "{filename}", line {lineno}, in {name}')
                if line:
                    traces.append(f"  {line.strip()}")
        raise BadRequest(f"{traces}\n{exc_txt}")


class PersistentClass:
    @classmethod
    def get_by_id(cls, sess, oid):
        obj = sess.execute(select(cls).where(cls.id == oid)).scalar_one_or_none()
        if obj is None:
            raise NotFound(f"There isn't a {cls.__name__} with the id {oid}")
        return obj

    def _eq_(self, other):
        return type(other) is type(self) and other.id == self.id


class GReadType(Base, PersistentClass):
    __tablename__ = "g_read_type"
    id = Column("id", Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)

    def __init__(self, code, description):
        self.code = code
        self.description = description

    @staticmethod
    def insert(sess, code, description):
        g_read_type = GReadType(code, description)
        sess.add(g_read_type)
        return g_read_type

    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        typ = sess.query(GReadType).filter_by(code=code).first()
        if typ is None:
            raise BadRequest("The Read Type with code " + code + " can't be found.")
        return typ


class Snag(Base, PersistentClass):
    NEGATIVE = "Negative values"
    ESTIMATED = "Estimated"
    MISSING = "Missing"
    DATA_IGNORED = "Data ignored"

    @staticmethod
    def get_covered_snags(sess, site, channel, description, start_date, finish_date):
        query = (
            sess.query(Snag)
            .filter(
                Snag.channel == channel,
                Snag.site == site,
                Snag.description == description,
                or_(Snag.finish_date == null(), Snag.finish_date >= start_date),
            )
            .order_by(Snag.start_date)
        )
        if finish_date is not None:
            query = query.filter(Snag.start_date <= finish_date)
        return query.all()

    @staticmethod
    def insert_snag(sess, site, channel, description, start_date, finish_date):
        snag = Snag(site, channel, description, start_date, finish_date)
        sess.add(snag)
        return snag

    @staticmethod
    def add_snag(sess, site, channel, description, start_date, finish_date):
        background_start = start_date
        for snag in Snag.get_covered_snags(
            sess, site, channel, description, start_date, finish_date
        ):
            if hh_before(background_start, snag.start_date):
                Snag.insert_snag(
                    sess,
                    site,
                    channel,
                    description,
                    background_start,
                    snag.start_date - HH,
                )

            background_start = (
                None if snag.finish_date is None else snag.finish_date + HH
            )

        if background_start is not None and not hh_after(background_start, finish_date):
            Snag.insert_snag(
                sess, site, channel, description, background_start, finish_date
            )

        prev_snag = None
        for snag in Snag.get_covered_snags(
            sess,
            site,
            channel,
            description,
            start_date - HH,
            None if finish_date is None else finish_date + HH,
        ):
            if (
                prev_snag is not None
                and (prev_snag.finish_date + HH) == snag.start_date
                and prev_snag.is_ignored == snag.is_ignored
            ):
                prev_snag.update(prev_snag.start_date, snag.finish_date)
                sess.delete(snag)
            else:
                prev_snag = snag

    @staticmethod
    def remove_snag(sess, site, channel, description, start_date, finish_date):
        for snag in Snag.get_covered_snags(
            sess, site, channel, description, start_date, finish_date
        ):
            out_left = snag.start_date < start_date
            out_right = hh_after(snag.finish_date, finish_date)
            if out_left and out_right:
                Snag.insert_snag(
                    sess, site, channel, description, finish_date + HH, snag.finish_date
                )
                snag.finish_date = start_date - HH
            elif out_left:
                snag.finish_date = start_date - HH
            elif out_right:
                snag.start_date = finish_date + HH
            else:
                sess.delete(snag)
            sess.flush()

    __tablename__ = "snag"
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("site.id"), index=True)
    channel_id = Column(Integer, ForeignKey("channel.id"), index=True)
    date_created = Column(DateTime(timezone=True), nullable=False, index=True)
    is_ignored = Column(Boolean, nullable=False, index=True)
    description = Column(String, nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    finish_date = Column(DateTime(timezone=True), index=True)

    def __init__(self, site, channel, description, start_date, finish_date):
        if site is None and channel is None:
            raise BadRequest("The site and channel can't both be null.")
        if site is not None and channel is not None:
            raise BadRequest("The site and channel can't both be present.")
        self.site = site
        self.channel = channel

        self.date_created = utc_datetime_now()
        self.description = description
        self.is_ignored = False
        self.update(start_date, finish_date)

    def update(self, start_date, finish_date):
        if start_date is None:
            raise BadRequest("The snag start date can't be null.")
        if hh_after(start_date, finish_date):
            raise BadRequest("Start date can't be after finish date.")
        self.start_date = start_date
        self.finish_date = finish_date

    def set_is_ignored(self, ignore):
        if not self.is_ignored and ignore and self.finish_date is None:
            raise BadRequest("An ongoing snag cannot be ignored.")
        self.is_ignored = ignore


class GspGroup(Base, PersistentClass):
    @staticmethod
    def insert(sess, code, description):
        gsp_group = GspGroup(code, description)
        sess.add(gsp_group)
        return gsp_group

    @staticmethod
    def find_by_code(sess, code):
        code = code.strip()
        return sess.execute(
            select(GspGroup).where(GspGroup.code == code)
        ).scalar_one_or_none()

    @staticmethod
    def get_by_code(sess, code):
        group = GspGroup.find_by_code(sess, code)
        if group is None:
            raise BadRequest(f"The GSP group with code {code} can't be found.")
        return group

    __tablename__ = "gsp_group"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    supplies = relationship("Supply", backref="gsp_group")

    def __init__(self, code, description):
        self.code = code
        self.description = description


class VoltageLevel(Base, PersistentClass):
    __tablename__ = "voltage_level"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    llfcs = relationship("Llfc", backref="voltage_level")

    def __init__(self, code, name):
        self.code = code
        self.name = name

    @classmethod
    def insert(cls, sess, code, name):
        voltage_level = cls(code, name)
        sess.add(voltage_level)
        sess.flush()
        return voltage_level

    @staticmethod
    def get_by_code(sess, code):
        vl = sess.execute(
            select(VoltageLevel).where(VoltageLevel.code == code)
        ).scalar_one_or_none()
        if vl is None:
            raise BadRequest(f"There is no voltage level with the code '{code}'.")
        return vl


class GeneratorType(Base, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        gen_type = sess.query(GeneratorType).filter_by(code=code).first()
        if gen_type is None:
            raise BadRequest(f"There's no generator type with the code '{code}'")
        return gen_type

    __tablename__ = "generator_type"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    supplies = relationship("Supply", backref="generator_type")

    def __init__(self, code, description):
        self.code = code
        self.description = description


class Source(Base, PersistentClass):
    @staticmethod
    def insert(sess, code, description):
        source = Source(code, description)
        sess.add(source)
        return source

    @staticmethod
    def get_by_code(sess, code):
        source = sess.query(Source).filter_by(code=code.strip()).first()
        if source is None:
            raise BadRequest("There's no source with the code '" + code + "'")
        return source

    __tablename__ = "source"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    supplies = relationship("Supply", backref="source")

    def __init__(self, code, name):
        self.code = code
        self.name = name


class ReadType(Base, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        typ = sess.query(ReadType).filter_by(code=code).first()
        if typ is None:
            raise BadRequest(f"The Read Type with code '{code}' can't be found.")
        return typ

    __tablename__ = "read_type"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)

    def __init__(self, code, description):
        self.code = code
        self.description = description

    @classmethod
    def insert(cls, sess, code, description):
        read_type = cls(code, description)
        sess.add(read_type)
        return read_type


class Cop(Base, PersistentClass):
    @staticmethod
    def insert(sess, code, desc):
        cop = Cop(code, desc)
        sess.add(cop)
        return cop

    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        typ = sess.query(Cop).filter_by(code=code).first()
        if typ is None:
            raise BadRequest(f"The CoP with code {code} can't be found.")
        return typ

    @staticmethod
    def get_valid(sess, meter_type):

        if meter_type.code == "C5":
            q = select(Cop).where(Cop.code.in_(["1", "2", "3", "4", "5"]))
        elif meter_type.code in ["6A", "6B", "6C", "6D"]:
            q = select(Cop).where(Cop.code == meter_type.code.lower())
        else:
            q = select(Cop)
        return sess.scalars(q.order_by(Cop.code))

    __tablename__ = "cop"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    eras = relationship("Era", backref="cop")

    def __init__(self, code, description):
        self.code = code
        self.description = description


class Comm(Base, PersistentClass):
    @staticmethod
    def insert(sess, code, desc):
        comm = Comm(code, desc)
        sess.add(comm)
        return comm

    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        comm = sess.execute(select(Comm).where(Comm.code == code)).scalar_one_or_none()
        if comm is None:
            raise BadRequest(f"The Comm with code {code} can't be found.")
        return comm

    __tablename__ = "comm"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    eras = relationship("Era", backref="comm")

    def __init__(self, code, description):
        self.code = code
        self.description = description


class RegisterRead(Base, PersistentClass):
    UNITS_INT = {0: "kWh", 1: "kVArh", 2: "kW", 3: "kVA"}
    UNITS_STR = {"kWh": 0, "kVArh": 1, "kW": 2, "kVA": 3}

    @staticmethod
    def units_to_int(units_str):
        try:
            return RegisterRead.UNITS_STR[units_str]
        except KeyError:
            raise BadRequest(f"The units '{units_str}' isn't recognized.")

    __tablename__ = "register_read"
    id = Column(Integer, primary_key=True)
    bill_id = Column(
        Integer, ForeignKey("bill.id", ondelete="CASCADE"), nullable=False, index=True
    )
    msn = Column(String, nullable=False)
    mpan_str = Column(String, nullable=False)
    coefficient = Column(Numeric, nullable=False)
    units = Column(Integer, nullable=False, index=True)
    tpr_id = Column(Integer, ForeignKey("tpr.id"))
    previous_date = Column(DateTime(timezone=True), nullable=False)
    previous_value = Column(Numeric, nullable=False)
    previous_type_id = Column(Integer, ForeignKey("read_type.id"))
    previous_type = relationship(
        "ReadType", primaryjoin="ReadType.id==RegisterRead.previous_type_id"
    )
    present_date = Column(DateTime(timezone=True), nullable=False)
    present_value = Column(Numeric, nullable=False)
    present_type_id = Column(Integer, ForeignKey("read_type.id"))
    present_type = relationship(
        "ReadType", primaryjoin="ReadType.id==RegisterRead.present_type_id"
    )
    __table_args__ = (
        UniqueConstraint(
            "bill_id",
            "msn",
            "mpan_str",
            "coefficient",
            "units",
            "tpr_id",
            "previous_date",
            "previous_value",
            "previous_type_id",
            "present_date",
            "present_value",
            "present_type_id",
        ),
    )

    def __init__(
        self,
        bill,
        tpr,
        coefficient,
        units,
        msn,
        mpan_str,
        previous_date,
        previous_value,
        previous_type,
        present_date,
        present_value,
        present_type,
    ):
        self.bill = bill
        self.update(
            tpr,
            coefficient,
            units,
            msn,
            mpan_str,
            previous_date,
            previous_value,
            previous_type,
            present_date,
            present_value,
            present_type,
        )

    def update(
        self,
        tpr,
        coefficient,
        units,
        msn,
        mpan_str,
        previous_date,
        previous_value,
        previous_type,
        present_date,
        present_value,
        present_type,
    ):
        if tpr is None and units == "kWh":
            raise BadRequest(
                "If a register read is measuring kWh, there must be a TPR."
            )
        if previous_value < 0 or present_value < 0:
            raise BadRequest("Negative register reads aren't allowed.")

        self.tpr = tpr
        self.coefficient = coefficient
        self.units = self.units_to_int(units)
        self.previous_date = previous_date
        self.previous_value = previous_value
        self.previous_type = previous_type
        self.present_date = present_date
        self.present_value = present_value
        self.present_type = present_type
        self.msn = msn
        self.mpan_str = mpan_str

    def delete(self, sess):
        sess.delete(self)
        sess.flush()

    def units_as_str(self):
        return self.UNITS_INT[self.units]


class BatchFile(Base, PersistentClass):
    __tablename__ = "batch_file"
    id = Column(Integer, primary_key=True)
    batch_id = Column(
        Integer, ForeignKey("batch.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename = Column(String, nullable=False, index=True)
    upload_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    data = Column(LargeBinary, nullable=False)
    parser_name = Column(String, nullable=False)

    def __init__(self, batch, filename, data, parser_name):
        self.batch = batch
        self.filename = filename
        self.data = data
        self.upload_timestamp = utc_datetime_now()
        self.parser_name = parser_name

    def update(self, parser_name):
        self.parser_name = parser_name

    def delete(self, sess):
        sess.delete(self)
        sess.flush()


class Bill(Base, PersistentClass):
    __tablename__ = "bill"
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("batch.id"), nullable=False, index=True)
    supply_id = Column(Integer, ForeignKey("supply.id"), nullable=False)
    issue_date = Column(DateTime(timezone=True), nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    finish_date = Column(DateTime(timezone=True), nullable=False, index=True)
    net = Column(Numeric, nullable=False)
    vat = Column(Numeric, nullable=False)
    gross = Column(Numeric, nullable=False)
    account = Column(String, nullable=False)
    reference = Column(String, nullable=False, index=True)
    bill_type_id = Column(Integer, ForeignKey("bill_type.id"), index=True)
    bill_type = relationship("BillType")
    breakdown = Column(String, nullable=False)
    kwh = Column(Numeric, nullable=False)
    reads = relationship(
        "RegisterRead",
        backref="bill",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(
        self,
        batch,
        supply,
        account,
        reference,
        issue_date,
        start_date,
        finish_date,
        kwh,
        net,
        vat,
        gross,
        bill_type,
        breakdown,
    ):
        self.batch = batch
        self.supply = supply
        self.update(
            account,
            reference,
            issue_date,
            start_date,
            finish_date,
            kwh,
            net,
            vat,
            gross,
            bill_type,
            breakdown,
        )

    @property
    def bd(self):
        if not hasattr(self, "_bd"):
            self._bd = loads(self.breakdown)
        return self._bd

    def update(
        self,
        account,
        reference,
        issue_date,
        start_date,
        finish_date,
        kwh,
        net,
        vat,
        gross,
        bill_type,
        breakdown,
    ):
        self.reference = reference
        self.account = account
        if issue_date is None:
            raise Exception("The issue date may not be null.")

        self.issue_date = issue_date
        if start_date > finish_date:
            raise BadRequest(
                f"The bill start date {hh_format(start_date)} can't be after the "
                f"finish date {hh_format(finish_date)}."
            )

        self.start_date = start_date
        self.finish_date = finish_date
        if kwh is None:
            raise Exception("kwh can't be null.")

        if self.batch.contract.market_role.code != "X" and kwh != Decimal("0"):
            raise BadRequest("kWh can only be non-zero for a supplier bill.")

        self.kwh = kwh

        for val, name in ((net, "net"), (vat, "vat"), (gross, "gross")):
            if val.as_tuple().exponent > -2:
                raise BadRequest(
                    f"The '{name}' field of a bill must be written to at least two "
                    f"decimal places. It's actually {val}"
                )
        self.net = net
        self.vat = vat
        self.gross = gross
        if bill_type is None:
            raise Exception("Type can't be null.")

        self.bill_type = bill_type
        if isinstance(breakdown, Mapping):
            self.breakdown = dumps(breakdown)
        else:
            raise BadRequest("The 'breakdown' parameter must be a mapping type.")

    def insert_read(
        self,
        sess,
        tpr,
        coefficient,
        units,
        msn,
        mpan_str,
        prev_date,
        prev_value,
        prev_type,
        pres_date,
        pres_value,
        pres_type,
    ):
        read = RegisterRead(
            self,
            tpr,
            coefficient,
            units,
            msn,
            mpan_str,
            prev_date,
            prev_value,
            prev_type,
            pres_date,
            pres_value,
            pres_type,
        )
        sess.add(read)
        try:
            sess.flush()
        except IntegrityError as e:
            if (
                "duplicate key value violates unique constraint "
                '"register_read_bill_id_msn_mpan_str_coefficient_units_tpr_id_key"'
                in str(e)
            ):
                raise BadRequest("Duplicate register reads aren't allowed")
            else:
                raise
        return read

    def delete(self, sess):
        sess.delete(self)
        sess.flush()


class BillType(Base, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        bill_type = sess.query(BillType).filter(BillType.code == code).first()
        if bill_type is None:
            raise BadRequest(f"The bill type with code {code} can't be found.")
        return bill_type

    @staticmethod
    def insert(sess, code, description):
        bill_type = BillType(code, description)
        sess.add(bill_type)
        return bill_type

    __tablename__ = "bill_type"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)

    def __init__(self, code, description):
        self.code = code
        self.description = description


class Pc(Base, PersistentClass):
    @staticmethod
    def insert(sess, code, name, valid_from, valid_to):
        pc = Pc(code, name, valid_from, valid_to)
        sess.add(pc)
        return pc

    @staticmethod
    def find_by_code(sess, code):
        code = code.strip().zfill(2)
        return sess.execute(select(Pc).where(Pc.code == code)).scalar_one_or_none()

    @staticmethod
    def get_by_code(sess, code):
        pc = Pc.find_by_code(sess, code)
        if pc is None:
            raise BadRequest(f"The PC with code {code} can't be found.")
        return pc

    __tablename__ = "pc"
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    eras = relationship("Era", backref="pc")
    valid_mtc_llfc_ssc_pcs = relationship("MtcLlfcSscPc", backref="pc")
    __table_args__ = (UniqueConstraint("code", "valid_from"),)

    def __init__(self, code, name, valid_from, valid_to):
        self.code = code
        self.name = name
        self.valid_from = valid_from
        self.valid_to = valid_to


class Batch(Base, PersistentClass):
    __tablename__ = "batch"
    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("contract.id"), nullable=False)
    reference = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)
    bills = relationship("Bill", backref="batch")
    files = relationship(
        "BatchFile", backref="batch", cascade="all, delete-orphan", passive_deletes=True
    )

    def __init__(self, sess, contract, reference, description):
        self.contract = contract
        self._update(sess, reference, description)

    def _update(self, sess, reference, description):
        reference = reference.strip()
        if len(reference) == 0:
            raise BadRequest("The batch reference can't be blank.")

        self.reference = reference
        self.description = description.strip()

    def update(self, sess, reference, description):
        self._update(sess, reference, description)
        sess.flush()

    def delete(self, sess):
        sess.execute(delete(Bill).where(Bill.batch == self))
        sess.delete(self)

    def insert_bill(
        self,
        sess,
        account,
        reference,
        issue_date,
        start_date,
        finish_date,
        kwh,
        net,
        vat,
        gross,
        bill_type,
        breakdown,
        supply,
    ):
        with sess.no_autoflush:
            bill = Bill(
                self,
                supply,
                account,
                reference,
                issue_date,
                start_date,
                finish_date,
                kwh,
                net,
                vat,
                gross,
                bill_type,
                breakdown,
            )

        sess.add(bill)
        sess.flush()
        return bill

    def insert_file(self, sess, name, data, parser_name):
        batch_file = BatchFile(self, name, data, parser_name)
        sess.add(batch_file)
        sess.flush()
        return batch_file

    @staticmethod
    def get_mop_by_id(sess, batch_id):
        batch = (
            sess.query(Batch)
            .join(Contract)
            .join(MarketRole)
            .filter(Batch.id == batch_id, MarketRole.code == "M")
            .first()
        )
        if batch is None:
            raise BadRequest(
                "The MOP batch with id {batch_id} can't be found.".format(
                    batch_id=batch_id
                )
            )
        return batch


class Party(Base, PersistentClass):
    __tablename__ = "party"
    id = Column(Integer, primary_key=True)
    market_role_id = Column(Integer, ForeignKey("market_role.id"), index=True)
    participant_id = Column(Integer, ForeignKey("participant.id"), index=True)
    name = Column(String, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    users = relationship("User", backref="party")
    dno_code = Column(String)
    contracts = relationship("Contract", back_populates="party")
    llfcs = relationship("Llfc", backref="dno")
    supplies = relationship("Supply", backref="dno")
    __table_args__ = (
        UniqueConstraint("market_role_id", "participant_id", "valid_from"),
    )

    def __init__(self, participant, market_role, name, valid_from, valid_to, dno_code):
        self.participant = participant
        self.market_role = market_role
        self.name = name
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.dno_code = dno_code

    def find_llfc_by_code(self, sess, code, date):
        code = code.zfill(3)
        q = select(Llfc).where(Llfc.dno == self, Llfc.code == code)

        if date is None:
            q = q.where(Llfc.valid_to == null())
        else:
            q = q.where(
                Llfc.valid_from <= date,
                or_(Llfc.valid_to == null(), Llfc.valid_to >= date),
            )
        return sess.execute(q).scalar_one_or_none()

    def get_llfc_by_code(self, sess, code, date):
        llfc = self.find_llfc_by_code(sess, code, date)
        if llfc is None:
            raise BadRequest(
                f"There is no LLFC with the code '{code}' associated with the DNO "
                f"{self.dno_code} at the date {hh_format(date)}."
            )
        return llfc

    def insert_llfc(
        self,
        sess,
        code,
        description,
        voltage_level,
        is_substation,
        is_import,
        valid_from,
        valid_to,
    ):
        if self.market_role.code == "R":
            llfc = Llfc(
                self,
                code,
                description,
                voltage_level,
                is_substation,
                is_import,
                valid_from,
                valid_to,
            )
            sess.add(llfc)
            sess.flush()
            return llfc
        else:
            raise BadRequest("This party isn't a DNO.")

    @classmethod
    def insert(
        cls, sess, participant, market_role, name, valid_from, valid_to, dno_code
    ):
        party = Party(participant, market_role, name, valid_from, valid_to, dno_code)
        sess.add(party)
        sess.flush()
        return party

    @staticmethod
    def find_by_participant_role(sess, participant, market_role, valid_from):
        return sess.execute(
            select(Party).where(
                Party.participant == participant,
                Party.market_role == market_role,
                Party.valid_from == valid_from,
            )
        ).scalar_one_or_none()

    @staticmethod
    def get_by_participant_role(sess, participant, market_role, valid_from):
        party = Party.find_by_participant_role(participant, market_role, valid_from)
        if party is None:
            raise BadRequest(
                f"There isn't a party with participant {participant} and market role "
                f"{market_role} at {hh_format(valid_from)}."
            )
        return party

    @staticmethod
    def find_by_participant_code_role_code(
        sess, participant_code, market_role_code, date
    ):
        q = (
            select(Party)
            .join(Participant)
            .join(MarketRole)
            .where(
                Participant.code == participant_code,
                MarketRole.code == market_role_code,
            )
        )
        if date is None:
            q = q.where(Party.valid_to == null())
        else:
            q = q.where(
                Party.valid_from <= date,
                or_(Party.valid_to == null(), Party.valid_to >= date),
            )
        return sess.execute(q).scalar_one_or_none()

    @staticmethod
    def get_by_participant_code_role_code(
        sess, participant_code, market_role_code, valid_from
    ):
        party = Party.find_by_participant_code_role_code(
            sess, participant_code, market_role_code, valid_from
        )
        if party is None:
            raise BadRequest(
                f"There isn't a party with participant code {participant_code} and "
                f"market role code {market_role_code} at {hh_format(valid_from)}"
            )
        return party

    @staticmethod
    def get_by_participant_id_role_code(sess, participant_id, market_role_code):
        party = (
            sess.query(Party)
            .join(MarketRole)
            .filter(
                Party.participant_id == participant_id,
                MarketRole.code == market_role_code,
            )
            .first()
        )
        if party is None:
            raise BadRequest(
                f"There isn't a party with participant id {participant_id} "
                f"and market role code {market_role_code}"
            )
        return party

    @staticmethod
    def find_dno_by_code(sess, dno_code, date):
        q = (
            select(Party)
            .join(MarketRole)
            .where(Party.dno_code == dno_code, MarketRole.code == "R")
        )
        if date is None:
            q = q.where(Party.valid_to == null())
        else:
            q = q.where(
                Party.valid_from <= date,
                or_(Party.valid_to == null(), Party.valid_to >= date),
            )
        return sess.execute(q).scalar_one_or_none()

    @classmethod
    def get_dno_by_code(cls, sess, dno_code, date):
        dno = cls.find_dno_by_code(sess, dno_code, date)
        if dno is None:
            raise BadRequest(
                f"There is no DNO with the code '{dno_code}' at time "
                f"{hh_format(date)}."
            )
        return dno

    @staticmethod
    def get_dno_by_id(sess, dno_id):
        dno = (
            sess.query(Party)
            .filter(Party.id == dno_id, Party.dno_code != null())
            .first()
        )
        if dno is None:
            raise BadRequest(f"There is no DNO with the id '{dno_id}'.")
        return dno


class Contract(Base, PersistentClass):
    @staticmethod
    def find_non_core_by_name(sess, name):
        return Contract.find_by_role_code_name(sess, "Z", name)

    @staticmethod
    def get_non_core_by_name(sess, name):
        return Contract.get_by_role_code_name(sess, "Z", name)

    @staticmethod
    def get_dc_by_id(sess, oid):
        return Contract.get_by_role_code_id(sess, "C", oid)

    @staticmethod
    def get_dc_by_name(sess, name):
        return Contract.get_by_role_code_name(sess, "C", name)

    @staticmethod
    def find_dno_by_name(sess, name):
        return Contract.find_by_role_code_name(sess, "R", name)

    @staticmethod
    def get_dno_by_name(sess, name):
        return Contract.get_by_role_code_name(sess, "R", name)

    @staticmethod
    def get_mop_by_id(sess, oid):
        return Contract.get_by_role_code_id(sess, "M", oid)

    @staticmethod
    def get_mop_by_name(sess, name):
        return Contract.get_by_role_code_name(sess, "M", name)

    @staticmethod
    def get_supplier_by_id(sess, oid):
        return Contract.get_by_role_code_id(sess, "X", oid)

    @staticmethod
    def find_supplier_by_name(sess, name):
        return Contract.find_by_role_code_name(sess, "X", name)

    @staticmethod
    def get_supplier_by_name(sess, name):
        return Contract.get_by_role_code_name(sess, "X", name)

    @staticmethod
    def get_non_core_by_id(sess, oid):
        return Contract.get_by_role_code_id(sess, "Z", oid)

    @staticmethod
    def get_by_role_code_id(sess, role_code, oid):
        cont = Contract.find_by_role_code_id(sess, role_code, oid)
        if cont is None:
            raise NotFound(
                f"There isn't a contract with the role code '{role_code}' and id "
                f"'{oid}'."
            )
        return cont

    @staticmethod
    def find_by_role_code_id(sess, role_code, oid):
        return (
            sess.query(Contract)
            .join(MarketRole)
            .filter(MarketRole.code == role_code, Contract.id == oid)
            .first()
        )

    @staticmethod
    def get_by_role_code_name(sess, role_code, name):
        cont = Contract.find_by_role_code_name(sess, role_code, name)
        if cont is None:
            raise BadRequest(
                f"There isn't a contract with the role code '{role_code}' and name "
                f"'{name}'."
            )
        return cont

    @staticmethod
    def find_by_role_code_name(sess, role_code, name):
        return (
            sess.query(Contract)
            .join(MarketRole)
            .filter(MarketRole.code == role_code, Contract.name == name)
            .first()
        )

    @staticmethod
    def insert_mop(
        sess,
        name,
        participant,
        charge_script,
        properties,
        start_date,
        finish_date,
        rate_script,
    ):
        return Contract.insert(
            sess,
            name,
            participant,
            "M",
            charge_script,
            properties,
            start_date,
            finish_date,
            rate_script,
        )

    @staticmethod
    def insert_non_core(
        sess, name, charge_script, properties, start_date, finish_date, rate_script
    ):
        return Contract.insert(
            sess,
            name,
            Participant.get_by_code(sess, "CALB"),
            "Z",
            charge_script,
            properties,
            start_date,
            finish_date,
            rate_script,
        )

    @staticmethod
    def insert_dc(
        sess,
        name,
        participant,
        charge_script,
        properties,
        start_date,
        finish_date,
        rate_script,
    ):
        return Contract.insert(
            sess,
            name,
            participant,
            "C",
            charge_script,
            properties,
            start_date,
            finish_date,
            rate_script,
        )

    @staticmethod
    def insert_supplier(
        sess,
        name,
        participant,
        charge_script,
        properties,
        start_date,
        finish_date,
        rate_script,
    ):
        return Contract.insert(
            sess,
            name,
            participant,
            "X",
            charge_script,
            properties,
            start_date,
            finish_date,
            rate_script,
        )

    @classmethod
    def insert_dno(
        cls,
        sess,
        name,
        participant,
        charge_script,
        properties,
        start_date,
        finish_date,
        rate_script,
    ):
        return cls.insert(
            sess,
            name,
            participant,
            "R",
            charge_script,
            properties,
            start_date,
            finish_date,
            rate_script,
        )

    @staticmethod
    def insert(
        sess,
        name,
        participant,
        role_code,
        charge_script,
        properties,
        start_date,
        finish_date,
        rate_script,
    ):
        party = Party.get_by_participant_id_role_code(sess, participant.id, role_code)
        contract = Contract(name, party, charge_script, properties, {})
        sess.add(contract)
        sess.flush()
        rscript = contract.insert_rate_script(sess, start_date, rate_script)
        contract.update_rate_script(sess, rscript, start_date, finish_date, rate_script)
        return contract

    __tablename__ = "contract"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    charge_script = Column(Text, nullable=False)
    properties = Column(Text, nullable=False)
    state = Column(Text, nullable=False)
    market_role_id = Column(Integer, ForeignKey("market_role.id"))
    __table_args__ = (UniqueConstraint("name", "market_role_id"),)
    rate_scripts = relationship(
        "RateScript",
        back_populates="contract",
        primaryjoin="Contract.id==RateScript.contract_id",
    )
    batches = relationship("Batch", backref="contract")
    party_id = Column(Integer, ForeignKey("party.id"))
    party = relationship("Party", back_populates="contracts")
    start_rate_script_id = Column(Integer, ForeignKey("rate_script.id"))
    finish_rate_script_id = Column(Integer, ForeignKey("rate_script.id"))

    start_rate_script = relationship(
        "RateScript", primaryjoin="RateScript.id==Contract.start_rate_script_id"
    )
    finish_rate_script = relationship(
        "RateScript", primaryjoin="RateScript.id==Contract.finish_rate_script_id"
    )

    def __init__(self, name, party, charge_script, properties, state):
        self.market_role = party.market_role
        self.update(name, party, charge_script, properties)
        self.update_state(state)

    def update(self, name, party, charge_script, properties):
        name = name.strip()
        if len(name) == 0:
            raise BadRequest("The contract name can't be blank.")
        self.name = name
        if party.market_role.id != self.market_role.id:
            raise BadRequest(
                "The market role of the party doesn't match the market role of the "
                "contract."
            )
        self.party = party
        try:
            parse(charge_script)
        except SyntaxError as e:
            raise BadRequest(str(e))
        except NameError as e:
            raise BadRequest(str(e))
        self.charge_script = charge_script
        self.update_properties(properties)

    def update_state(self, state):
        self.state = dumps(state)

    def update_properties(self, properties):
        self.properties = dumps(properties)

    def update_rate_script(self, sess, rscript, start_date, finish_date, script):
        if rscript.contract != self:
            raise Exception("This rate script doesn't below to this contract.")

        if start_date is None:
            raise BadRequest("The start date can't be None.")

        if hh_after(start_date, finish_date):
            raise BadRequest("The start date can't be after the finish date.")

        if not isinstance(script, Mapping):
            raise Exception("The script must be a Mapping type.")
        rscript.script = dumps(script)

        prev_rscript = self.find_rate_script_at(sess, rscript.start_date - HH)
        if rscript.finish_date is None:
            next_rscript = None
        else:
            next_rscript = self.find_rate_script_at(sess, rscript.finish_date + HH)

        rscript.start_date = start_date
        rscript.finish_date = finish_date

        if prev_rscript is not None:
            if not hh_before(prev_rscript.start_date, start_date):
                raise BadRequest(
                    """The start date must be after the start
                        date of the previous rate script."""
                )
            prev_rscript.finish_date = prev_hh(start_date)

        if next_rscript is not None:
            if finish_date is None:
                raise BadRequest(
                    """The finish date must be before the start date of the
                    next rate script."""
                )

            if not hh_before(finish_date, next_rscript.finish_date):
                raise BadRequest(
                    "The finish date must be before the finish date of the next rate "
                    "script."
                )

            next_rscript.start_date = next_hh(finish_date)

        sess.flush()
        rscripts = (
            sess.query(RateScript)
            .filter(RateScript.contract == self)
            .order_by(RateScript.start_date)
            .all()
        )
        self.start_rate_script = rscripts[0]
        self.finish_rate_script = rscripts[-1]

        eras_before = (
            sess.query(Era)
            .filter(
                Era.start_date < self.start_rate_script.start_date,
                or_(
                    Era.imp_supplier_contract == self,
                    Era.exp_supplier_contract == self,
                    Era.dc_contract == self,
                    Era.mop_contract == self,
                ),
            )
            .all()
        )
        if len(eras_before) > 0:
            mpan_core = eras_before[0].imp_mpan_core
            if mpan_core is None:
                mpan_core = eras_before[0].exp_mpan_core
            raise BadRequest(
                f"The era with MPAN core {mpan_core} exists before the start of this "
                f"contract, and is attached to this contract."
            )

        if self.finish_rate_script.finish_date is not None:
            eras_after = (
                sess.query(Era)
                .filter(
                    Era.finish_date > self.finish_rate_script.finish_date,
                    or_(
                        Era.imp_supplier_contract == self,
                        Era.exp_supplier_contract == self,
                        Era.dc_contract == self,
                        Era.mop_contract == self,
                    ),
                )
                .all()
            )
            if len(eras_after) > 0:
                mpan_core = eras_after[0].imp_mpan_core
                if mpan_core is None:
                    mpan_core = eras_after[0].exp_mpan_core
                raise BadRequest(
                    f"The era with MPAN core {mpan_core} exists after the start of "
                    f"this contract, and is attached to this contract."
                )

    def delete(self, sess):
        if len(self.batches) > 0:
            raise BadRequest("Can't delete a contract that has batches.")
        self.rate_scripts[:] = []
        sess.delete(self)

    def find_rate_script_at(self, sess, date):
        return (
            sess.query(RateScript)
            .filter(
                RateScript.contract == self,
                RateScript.start_date <= date,
                or_(RateScript.finish_date == null(), RateScript.finish_date >= date),
            )
            .first()
        )

    def start_date(self):
        return self.start_rate_script.start_date

    def finish_date(self):
        return self.finish_rate_script.finish_date

    def delete_rate_script(self, sess, rscript):
        rscripts = (
            sess.query(RateScript)
            .filter(RateScript.contract == self)
            .order_by(RateScript.start_date)
            .all()
        )

        if len(rscripts) < 2:
            raise BadRequest("You can't delete the last rate script.")
        if rscripts[0] == rscript:
            self.start_rate_script = rscripts[1]
        elif rscripts[-1] == rscript:
            self.finish_rate_script = rscripts[-2]

        sess.flush()
        sess.delete(rscript)
        sess.flush()

        if rscripts[0] == rscript:
            rscripts[1].start_date = rscript.start_date
        elif rscripts[-1] == rscript:
            rscripts[-2].finish_date = rscript.finish_date
        else:
            prev_script = self.find_rate_script_at(sess, prev_hh(rscript.start_date))
            prev_script.finish_date = rscript.finish_date

    def insert_rate_script(self, sess, start_date, script):
        scripts = (
            sess.query(RateScript)
            .filter(RateScript.contract == self)
            .order_by(RateScript.start_date)
            .all()
        )
        if len(scripts) == 0:
            finish_date = None
        else:
            if hh_after(start_date, scripts[-1].finish_date):
                raise BadRequest(
                    f"For the contract {self.id} called {self.name}, the start date "
                    f"{start_date} is after the last rate script."
                )

            covered_script = self.find_rate_script_at(sess, start_date)
            if covered_script is None:
                finish_date = prev_hh(scripts[0].start_date)
            else:
                if covered_script.start_date == covered_script.finish_date:
                    raise BadRequest(
                        "The start date falls on a rate script which is only "
                        "half an hour in length, and so cannot be divided."
                    )
                if start_date == covered_script.start_date:
                    raise BadRequest(
                        "The start date is the same as the start date of an "
                        "existing rate script."
                    )

                finish_date = covered_script.finish_date
                covered_script.finish_date = prev_hh(start_date)
                sess.flush()

        new_script = RateScript(self, start_date, finish_date, script)
        sess.add(new_script)
        sess.flush()
        rscripts = (
            sess.query(RateScript)
            .filter(RateScript.contract == self)
            .order_by(RateScript.start_date)
            .all()
        )
        self.start_rate_script = rscripts[0]
        self.finish_rate_script = rscripts[-1]
        sess.flush()
        return new_script

    def insert_batch(self, sess, reference, description):
        batch = Batch(sess, self, reference, description)
        try:
            sess.add(batch)
            sess.flush()
        except IntegrityError as e:
            if (
                'duplicate key value violates unique constraint "batch_reference_key"'
                in str(e)
            ):
                raise BadRequest(
                    f"There's already a batch with the reference '{reference}'."
                ) from e
            else:
                raise e
        return batch

    def make_properties(self):
        return loads(self.properties)

    def make_state(self):
        return loads(self.state)

    def get_batch(self, sess, reference):
        batch = (
            sess.query(Batch)
            .filter(Batch.contract == self, Batch.reference == reference)
            .first()
        )
        if batch is None:
            raise BadRequest(f"The batch '{reference}' can't be found.")
        return batch

    def get_next_batch_details(self, sess):
        batch = (
            sess.query(Batch)
            .filter(Batch.contract == self)
            .order_by(Batch.reference.desc())
            .first()
        )
        if batch is None:
            ref = desc = ""
        else:
            last = batch.reference
            digits = "".join(list(takewhile(str.isdigit, last[::-1]))[::-1])
            prefix = last[: len(last) - len(digits)]
            if len(digits) > 0:
                suffix = str(int(digits) + 1).zfill(len(digits))
            else:
                suffix = ""
            ref = prefix + suffix
            desc = batch.description

        return ref, desc


class Site(Base, PersistentClass):
    __tablename__ = "site"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    site_eras = relationship("SiteEra", backref="site")
    site_g_eras = relationship("SiteGEra", backref="site")
    snags = relationship("Snag", backref="site")

    def update(self, code, name):
        code = code.strip()
        if len(code) == 0:
            raise BadRequest("The site code can't be blank.")
        self.code = code
        self.name = name

    def __init__(self, code, name):
        self.update(code, name)

    def delete(self, sess):
        if len(self.site_eras) > 0:
            raise BadRequest(
                "This site can't be deleted while there are still eras attached to it."
            )

        for snag in self.snags:
            snag.delete(sess)
        sess.flush()
        sess.delete(self)
        sess.flush()

    def hh_data(self, sess, start_date, finish_date, exclude_virtual=False):
        cache = {}
        keys = {
            "net": {True: ["imp_net"], False: ["exp_net"]},
            "gen-net": {True: ["imp_net", "exp_gen"], False: ["exp_net", "imp_gen"]},
            "gen": {True: ["imp_gen"], False: ["exp_gen"]},
            "3rd-party": {True: ["imp_3p"], False: ["exp_3p"]},
            "3rd-party-reverse": {True: ["exp_3p"], False: ["imp_3p"]},
        }
        data = []

        channel_q = (
            select(Channel.id)
            .join(Era)
            .join(SiteEra)
            .join(Supply)
            .join(Source)
            .where(
                SiteEra.site == self,
                SiteEra.is_physical == true(),
                Era.start_date <= finish_date,
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
                Source.code != "sub",
                Channel.channel_type == "ACTIVE",
            )
        )
        if exclude_virtual:
            channel_q = channel_q.join(Party).where(Party.dno_code != "88")

        channel_ids = list(sess.execute(channel_q).scalars())

        db_data = iter(
            sess.query(
                HhDatum.start_date, HhDatum.value, Channel.imp_related, Source.code
            )
            .join(Channel)
            .join(Era)
            .join(Supply)
            .join(Source)
            .filter(
                HhDatum.channel_id.in_(channel_ids),
                HhDatum.start_date >= start_date,
                HhDatum.start_date <= finish_date,
            )
            .order_by(HhDatum.start_date)
        )

        start, value, imp_related, source_code = next(db_data, (None, None, None, None))

        for hh_start in hh_range(cache, start_date, finish_date):
            dd = {
                "start_date": hh_start,
                "imp_net": 0,
                "exp_net": 0,
                "imp_gen": 0,
                "exp_gen": 0,
                "imp_3p": 0,
                "exp_3p": 0,
            }
            data.append(dd)
            while start == hh_start:
                for key in keys[source_code][imp_related]:
                    dd[key] += value
                start, value, imp_related, source_code = next(
                    db_data, (None, None, None, None)
                )

            dd["displaced"] = dd["imp_gen"] - dd["exp_gen"] - dd["exp_net"]
            dd["used"] = dd["displaced"] + dd["imp_net"] + dd["imp_3p"] - dd["exp_3p"]

        return data

    @staticmethod
    def insert(sess, code, name):
        site = Site(code, name)
        try:
            sess.add(site)
            sess.flush()
        except IntegrityError as e:
            if 'duplicate key value violates unique constraint "site_code_key"' in str(
                e
            ):
                raise BadRequest("There's already a site with this code.")
            if 'duplicate key value violates unique constraint "site_name_key"' in str(
                e
            ):
                raise BadRequest("There's already a site with this name.")
            else:
                raise e
        return site

    @staticmethod
    def find_by_code(sess, code):
        return sess.query(Site).filter_by(code=code).first()

    @staticmethod
    def get_by_code(sess, code):
        site = Site.find_by_code(sess, code)
        if site is None:
            raise BadRequest(f"There isn't a site with the code {code}.")
        return site

    def find_linked_sites(self, sess, start_date, finish_date):
        site_era_alias = aliased(SiteEra)
        return (
            sess.query(Site)
            .join(SiteEra)
            .join(Era)
            .join(site_era_alias)
            .filter(
                Site.id != self.id,
                site_era_alias.site == self,
                Era.start_date <= finish_date,
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
            )
            .distinct()
            .order_by(Site.code)
            .all()
        )

    def insert_e_supply(
        self,
        sess,
        source,
        generator_type,
        supply_name,
        start_date,
        finish_date,
        gsp_group,
        mop_contract,
        mop_account,
        dc_contract,
        dc_account,
        msn,
        dno,
        pc,
        old_mtc_code,
        cop,
        comm,
        ssc,
        energisation_status,
        properties,
        imp_mpan_core,
        imp_llfc_code,
        imp_supplier_contract,
        imp_supplier_account,
        imp_sc,
        exp_mpan_core,
        exp_llfc_code,
        exp_supplier_contract,
        exp_supplier_account,
        exp_sc,
    ):
        mpan_core = exp_mpan_core if imp_mpan_core is None else imp_mpan_core
        if mpan_core is None:
            raise BadRequest(
                "An era must have either an import or export MPAN core or both."
            )
        supply = Supply(supply_name, source, generator_type, gsp_group, dno)

        try:
            sess.add(supply)
            sess.flush()
        except SQLAlchemyError as e:
            sess.rollback()
            raise e

        supply.insert_era(
            sess,
            self,
            [],
            start_date,
            finish_date,
            mop_contract,
            mop_account,
            dc_contract,
            dc_account,
            msn,
            pc,
            old_mtc_code,
            cop,
            comm,
            ssc,
            energisation_status,
            properties,
            imp_mpan_core,
            imp_llfc_code,
            imp_supplier_contract,
            imp_supplier_account,
            imp_sc,
            exp_mpan_core,
            exp_llfc_code,
            exp_supplier_contract,
            exp_supplier_account,
            exp_sc,
            set(),
        )
        sess.flush()
        return supply

    def insert_g_supply(
        self,
        sess,
        mprn,
        supply_name,
        g_exit_zone,
        start_date,
        finish_date,
        msn,
        correction_factor,
        g_unit,
        g_contract,
        account,
        g_reading_frequency,
        aq,
        soq,
    ):
        if g_contract.is_industry:
            raise BadRequest(
                "The gas contract must be a supplier contract rather than an industry "
                "contract."
            )
        g_supply = GSupply(mprn, supply_name, g_exit_zone, "")

        try:
            sess.add(g_supply)
            sess.flush()
        except IntegrityError as e:
            sess.rollback()
            if (
                'duplicate key value violates unique constraint "g_supply_mprn_key"'
                in str(e)
            ):
                raise BadRequest("There's already a gas supply with that MPRN.")
            else:
                raise e

        g_supply.insert_g_era(
            sess,
            self,
            [],
            start_date,
            finish_date,
            msn,
            correction_factor,
            g_unit,
            g_contract,
            account,
            g_reading_frequency,
            aq,
            soq,
        )
        sess.flush()
        return g_supply

    def hh_check(self, sess, start, finish):
        for group in self.groups(sess, start, finish, False):
            group.hh_check(sess)

    def groups(self, sess, start, finish, primary_only):
        groups = []
        check_from = start
        check_to = finish
        while check_from <= finish:
            sites = []
            supplies = []
            sites.append(self)
            if self.walk_group(sess, sites, supplies, check_from, check_to):
                sites = sorted(
                    sites,
                    key=operator.attrgetter("_num_phys_sups", "code"),
                    reverse=True,
                )
                if not primary_only or sites[0] == self:
                    groups.append(SiteGroup(check_from, check_to, sites, supplies))

                check_from = next_hh(check_to)
                check_to = finish
            else:
                mins = (
                    int(
                        math.floor(
                            (check_to - check_from).total_seconds() / 2 / (60 * 30)
                        )
                    )
                    * 30
                )
                check_to = check_from + relativedelta(minutes=mins)
        return groups

    # return true if the supply is continuously attached to the site for the
    # given period.
    def walk_group(self, sess, group_sites, group_supplies, start, finish):
        new_site = group_sites[-1]
        new_site._num_phys_sups = (
            sess.query(SiteEra)
            .filter(SiteEra.site_id == new_site.id, SiteEra.is_physical == true())
            .count()
        )
        sups = (
            sess.query(Supply)
            .join(Era)
            .join(SiteEra)
            .filter(
                SiteEra.site == new_site,
                Era.start_date <= finish,
                or_(Era.finish_date == null(), Era.finish_date >= start),
            )
            .distinct()
            .all()
        )
        num_fit = len(
            sess.execute(
                text(
                    "select supply.id from supply, "
                    "era left join "
                    "(select site_era.era_id from site_era where "
                    "site_era.site_id = :site_id) as sera "
                    "on (era.id = sera.era_id) "
                    "where era.supply_id = supply.id and "
                    "era.start_date <= :finish_date and "
                    "(era.finish_date is null or era.finish_date >= :start_date) "
                    "group by supply.id having "
                    "bool_and(sera.era_id is not null) and "
                    "bool_or(era.start_date <= :start_date) and "
                    "bool_or(era.finish_date is null or "
                    "era.finish_date >= :finish_date)"
                ),
                {"site_id": new_site.id, "start_date": start, "finish_date": finish},
            ).fetchall()
        )

        if len(sups) == num_fit:
            for supply in sups:
                if supply not in group_supplies:
                    group_supplies.append(supply)
                    for site in (
                        sess.query(Site)
                        .join(SiteEra)
                        .join(Era)
                        .filter(
                            Era.supply_id == supply.id,
                            Era.start_date <= finish,
                            or_(Era.finish_date == null(), Era.finish_date >= start),
                            not_(Site.id.in_([s.id for s in group_sites])),
                        )
                        .distinct()
                    ):
                        group_sites.append(site)
                        if not self.walk_group(
                            sess, group_sites, group_supplies, start, finish
                        ):
                            return False
        else:
            return False
        return True


SALT_LENGTH = 16


class User(Base, PersistentClass):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email_address = Column(String, unique=True, nullable=False)
    password_digest = Column(String, nullable=False)
    user_role_id = Column(Integer, ForeignKey("user_role.id"))
    party_id = Column(Integer, ForeignKey("party.id"))

    def __init__(self, email_address, password, user_role, party):
        self.update(email_address, user_role, party)
        self.set_password(password)

    def update(self, email_address, user_role, party):
        self.email_address = email_address
        self.user_role = user_role
        if user_role.code == "party-viewer":
            if party is None:
                raise BadRequest("There must be a party if the role is party-viewer.")
            self.party = party
        else:
            self.party = None

    def password_matches(self, password):
        digest = unhexlify(self.password_digest.encode("ascii"))
        salt = digest[:SALT_LENGTH]
        dk = digest[SALT_LENGTH:]

        return pbkdf2_hmac("sha256", password.encode("utf8"), salt, 100000) == dk

    def set_password(self, password):
        salt = os.urandom(SALT_LENGTH)
        dk = pbkdf2_hmac("sha256", password.encode("utf8"), salt, 100000)
        self.password_digest = hexlify(salt + dk).decode("ascii")

    @staticmethod
    def insert(sess, email_address, password, user_role, party):
        try:
            user = User(email_address, password, user_role, party)
            sess.add(user)
            sess.flush()
        except IntegrityError as e:
            if (
                "duplicate key value violates unique "
                + 'constraint "user_email_address_key"'
                in str(e)
            ):
                raise BadRequest("There's already a user with this email address.")
            else:
                raise e
        return user

    @staticmethod
    def get_by_email_address(sess, email_address):
        user = sess.execute(
            select(User).where(User.email_address == email_address)
        ).scalar_one_or_none()
        if user is None:
            raise BadRequest(
                f"There isn't a user with the email address {email_address}."
            )
        return user


class UserRole(Base, PersistentClass):
    __tablename__ = "user_role"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    users = relationship("User", backref="user_role")

    def __init__(self, code):
        self.code = code

    @staticmethod
    def insert(sess, code):
        role = UserRole(code)
        sess.add(role)
        sess.flush()
        return role

    @staticmethod
    def get_by_code(sess, code):
        role = sess.query(UserRole).filter_by(code=code.strip()).first()
        if role is None:
            raise BadRequest("There isn't a user role with code " + code + ".")
        return role


class MarketRole(Base, PersistentClass):
    @staticmethod
    def insert(sess, code, description):
        market_role = MarketRole(code, description)
        sess.add(market_role)
        sess.flush()
        return market_role

    @staticmethod
    def find_by_code(sess, code):
        return sess.execute(
            select(MarketRole).where(MarketRole.code == code)
        ).scalar_one_or_none()

    @staticmethod
    def get_by_code(sess, code):
        role = MarketRole.find_by_code(sess, code)
        if role is None:
            raise BadRequest(f"A role with code {code} cannot be found.")
        return role

    __tablename__ = "market_role"
    id = Column(Integer, primary_key=True)
    code = Column(String(length=1), unique=True, nullable=False)
    description = Column(String, nullable=False, unique=True)
    contracts = relationship("Contract", backref="market_role")
    parties = relationship("Party", backref="market_role")

    def __init__(self, code, description):
        self.code = code
        self.description = description


class Participant(Base, PersistentClass):
    __tablename__ = "participant"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    parties = relationship("Party", backref="participant")
    mtc_participants = relationship("MtcParticipant", backref="participant")

    def __init__(self, code, name):
        self.code = code
        self.update(name)

    def update(self, name):
        self.name = name

    def insert_party(self, sess, market_role, name, valid_from, valid_to, dno_code):
        return Party.insert(
            sess, self, market_role, name, valid_from, valid_to, dno_code
        )

    def get_dno(self, sess):
        return sess.execute(
            select(Party)
            .join(MarketRole)
            .where(Party.participant == self, MarketRole.code == "R")
        ).scalar_one()

    @classmethod
    def insert(cls, sess, code, name):
        participant = cls(code, name)
        sess.add(participant)
        sess.flush()
        return participant

    @staticmethod
    def find_by_code(sess, code):
        return sess.execute(
            select(Participant).where(Participant.code == code)
        ).scalar_one_or_none()

    @staticmethod
    def get_by_code(sess, code):
        participant = Participant.find_by_code(sess, code)
        if participant is None:
            raise BadRequest(f"There isn't a Participant with code {code}.")
        return participant


class RateScript(Base, PersistentClass):
    @staticmethod
    def get_by_role_code_id(sess, market_role_code, oid):
        try:
            return sess.execute(
                select(RateScript)
                .join(Contract.rate_scripts)
                .join(MarketRole)
                .where(RateScript.id == oid, MarketRole.code == market_role_code)
            ).scalar_one()
        except NoResultFound:
            raise NotFound(
                f"There isn't a rate script with the id {oid} attached to a "
                f"contract with market role code {market_role_code}."
            )

    @staticmethod
    def get_dc_by_id(sess, oid):
        roles = ("C", "D")
        try:
            return sess.execute(
                select(RateScript)
                .join(Contract.rate_scripts)
                .join(MarketRole)
                .where(RateScript.id == oid, MarketRole.code.in_(roles))
            ).scalar_one()
        except NoResultFound:
            raise NotFound(
                f"There isn't a rate script with the id {oid} attached to a contract "
                f"with market role codes {roles}."
            )

    @staticmethod
    def get_supplier_by_id(sess, oid):
        return RateScript.get_by_role_code_id(sess, "X", oid)

    @staticmethod
    def get_non_core_by_id(sess, oid):
        return RateScript.get_by_role_code_id(sess, "Z", oid)

    @staticmethod
    def get_mop_by_id(sess, oid):
        return RateScript.get_by_role_code_id(sess, "M", oid)

    @staticmethod
    def get_dno_by_id(sess, oid):
        return RateScript.get_by_role_code_id(sess, "R", oid)

    __tablename__ = "rate_script"
    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("contract.id"))
    contract = relationship(
        "Contract",
        back_populates="rate_scripts",
        primaryjoin="Contract.id==RateScript.contract_id",
    )
    start_date = Column(DateTime(timezone=True), nullable=False)
    finish_date = Column(DateTime(timezone=True), nullable=True)
    script = Column(Text, nullable=False)

    def __init__(self, contract, start_date, finish_date, script):
        self.contract = contract
        self.start_date = start_date
        self.finish_date = finish_date
        self.update(script)

    def update(self, script):
        if not isinstance(script, Mapping):
            raise BadRequest("A script must be a Mapping type.")
        self.script = dumps(script)

    def make_script(self):
        return loads(self.script)


class Llfc(Base, PersistentClass):
    __tablename__ = "llfc"
    id = Column(Integer, primary_key=True)
    dno_id = Column(Integer, ForeignKey("party.id"))
    code = Column(String, nullable=False)
    description = Column(String)
    voltage_level_id = Column(Integer, ForeignKey("voltage_level.id"))
    is_substation = Column(Boolean, nullable=False)
    is_import = Column(Boolean, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    lafs = relationship("Laf", backref="llfc")
    mtc_llfcs = relationship("MtcLlfc", backref="llfc")
    mtc_llfc_sscs = relationship("MtcLlfcSsc", backref="llfc")
    __table_args__ = (UniqueConstraint("dno_id", "code", "valid_from"),)

    def __init__(
        self,
        dno,
        code,
        description,
        voltage_level,
        is_substation,
        is_import,
        valid_from,
        valid_to,
    ):
        self.dno = dno
        self.code = code
        self.update(
            description, voltage_level, is_substation, is_import, valid_from, valid_to
        )

    def update(
        self, description, voltage_level, is_substation, is_import, valid_from, valid_to
    ):
        self.description = description
        self.voltage_level = voltage_level
        self.is_substation = is_substation
        self.is_import = is_import
        self.valid_from = valid_from
        self.valid_to = valid_to

    def insert_laf(self, sess, timestamp, value):
        laf = Laf(self, timestamp, value)
        sess.add(laf)
        sess.flush()


class Laf(Base, PersistentClass):
    __tablename__ = "laf"
    id = Column(Integer, primary_key=True)
    llfc_id = Column(Integer, ForeignKey("llfc.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    value = Column(Numeric, nullable=False)
    __table_args__ = (UniqueConstraint("llfc_id", "timestamp"),)

    def __init__(
        self,
        llfc,
        timestamp,
        value,
    ):
        self.llfc = llfc
        self.timestamp = timestamp
        self.update(value)

    def update(self, value):
        self.value = value


# J0483 in https://www.electralink.co.uk/data-catalogues/dtc-catalogue/
class DtcMeterType(Base, PersistentClass):
    __tablename__ = "dtc_meter_type"
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)
    eras = relationship("Era", backref="dtc_meter_type")

    def __init__(self, code, description):
        self.code = code
        self.description = description

    @classmethod
    def insert(cls, sess, code, description):
        dtc_meter_type = cls(code, description)
        sess.add(dtc_meter_type)
        return dtc_meter_type

    @staticmethod
    def find_by_code(sess, code):
        return sess.execute(
            select(DtcMeterType).where(DtcMeterType.code == code)
        ).scalar_one_or_none()

    @classmethod
    def get_by_code(cls, sess, code):
        dtc_meter_type = cls.find_by_code(sess, code)
        if dtc_meter_type is None:
            raise Exception(f"Can't find the DTC meter type with code {code}.")
        return dtc_meter_type


class MeterType(Base, PersistentClass):
    __tablename__ = "meter_type"
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    description = Column(String, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    mtc_participants = relationship("MtcParticipant", backref="meter_type")
    __table_args__ = (UniqueConstraint("code", "valid_from"),)

    def __init__(self, code, description, valid_from, valid_to):
        self.code = code
        self.description = description
        self.valid_from = valid_from
        self.valid_to = valid_to

    @classmethod
    def insert(cls, sess, code, description, valid_from, valid_to):
        meter_type = cls(code, description, valid_from, valid_to)
        sess.add(meter_type)
        return meter_type

    @staticmethod
    def find_by_code(sess, code, date):
        q = select(MeterType).where(MeterType.code == code)
        if date is None:
            q = q.where(MeterType.valid_to == null())
        else:
            q = q.where(
                MeterType.valid_from <= date,
                or_(MeterType.valid_to == null(), MeterType.valid_to >= date),
            )
        return sess.execute(q).scalar_one_or_none()

    @classmethod
    def get_by_code(cls, sess, code, date):
        meter_type = cls.find_by_code(sess, code, date)
        if meter_type is None:
            raise Exception(
                f"Can't find the meter type with code {code} at {hh_format(date)}."
            )
        return meter_type


class MeterPaymentType(Base, PersistentClass):
    @classmethod
    def insert(cls, sess, code, description, valid_from, valid_to):
        meter_payment_type = cls(code, description, valid_from, valid_to)
        sess.add(meter_payment_type)
        sess.flush()
        return meter_payment_type

    @staticmethod
    def find_by_code(sess, code, date):
        q = select(MeterPaymentType).where(MeterPaymentType.code == code)
        if date is None:
            q = q.where(MeterPaymentType.valid_to == null())
        else:
            q = q.where(
                MeterPaymentType.valid_from <= date,
                or_(
                    MeterPaymentType.valid_to == null(),
                    MeterPaymentType.valid_to >= date,
                ),
            )
        return sess.execute(q).scalar_one_or_none()

    @classmethod
    def get_by_code(cls, sess, code, date):
        meter_payment_type = cls.find_by_code(sess, code, date)
        if meter_payment_type is None:
            raise Exception(f"Can't find the meter payment type with code {code}.")
        return meter_payment_type

    __tablename__ = "meter_payment_type"
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    description = Column(String, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    mtc_participants = relationship("MtcParticipant", backref="meter_payment_type")
    __table_args__ = (UniqueConstraint("code", "valid_from"),)

    def __init__(self, code, description, valid_from, valid_to):
        self.code = code
        self.description = description
        self.valid_from = valid_from
        self.valid_to = valid_to


class Mtc(Base, PersistentClass):
    __tablename__ = "mtc"
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, index=True)
    is_common = Column(Boolean, nullable=False)
    has_related_metering = Column(Boolean, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    mtc_participants = relationship("MtcParticipant", backref="mtc")
    __table_args__ = (UniqueConstraint("code", "valid_from"),)

    def __init__(
        self,
        code,
        is_common,
        has_related_metering,
        valid_from,
        valid_to,
    ):
        self.code = code
        self.valid_from = valid_from
        self.update(
            is_common,
            has_related_metering,
            valid_to,
        )

    def update(
        self,
        is_common,
        has_related_metering,
        valid_to,
    ):
        self.is_common = is_common
        self.has_related_metering = has_related_metering
        self.valid_to = valid_to

        if hh_after(self.valid_from, valid_to):
            raise BadRequest("The valid_from date can't be over the valid_to date.")

    @classmethod
    def insert(
        cls,
        sess,
        code,
        is_common,
        has_related_metering,
        valid_from,
        valid_to,
    ):
        mtc = cls(
            code,
            is_common,
            has_related_metering,
            valid_from,
            valid_to,
        )
        sess.add(mtc)
        sess.flush()
        return mtc

    @staticmethod
    def find_by_code(sess, code, date):
        code = code.zfill(3)
        q = select(Mtc).where(Mtc.code == code)
        if date is None:
            q = q.where(Mtc.valid_to == null())
        else:
            q = q.where(
                Mtc.valid_from <= date,
                or_(Mtc.valid_to == null(), Mtc.valid_to >= date),
            )
        return sess.execute(q).scalar_one_or_none()

    @classmethod
    def get_by_code(cls, sess, code, date):
        mtc = cls.find_by_code(sess, code, date)
        if mtc is None:
            raise BadRequest(
                f"There isn't an MTC with the code {code} at date {hh_format(date)}."
            )
        return mtc


class MtcParticipant(Base, PersistentClass):
    __tablename__ = "mtc_participant"
    id = Column(Integer, primary_key=True)
    mtc_id = Column(Integer, ForeignKey("mtc.id"), index=True)
    participant_id = Column(Integer, ForeignKey("participant.id"), index=True)
    description = Column(String, nullable=False)
    has_comms = Column(Boolean, nullable=False)
    is_hh = Column(Boolean, nullable=False)
    meter_type_id = Column(Integer, ForeignKey("meter_type.id"))
    meter_payment_type_id = Column(Integer, ForeignKey("meter_payment_type.id"))
    tpr_count = Column(Integer)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    eras = relationship("Era", backref="mtc_participant")
    mtc_sscs = relationship("MtcSsc", backref="mtc_participant")
    mtc_llfcs = relationship("MtcLlfc", backref="mtc_participant")
    __table_args__ = (UniqueConstraint("mtc_id", "participant_id", "valid_from"),)

    def __init__(
        self,
        mtc,
        participant,
        description,
        has_comms,
        is_hh,
        meter_type,
        meter_payment_type,
        tpr_count,
        valid_from,
        valid_to,
    ):
        self.mtc = mtc
        self.participant = participant
        self.update(
            description,
            has_comms,
            is_hh,
            meter_type,
            meter_payment_type,
            tpr_count,
            valid_from,
            valid_to,
        )

    def update(
        self,
        description,
        has_comms,
        is_hh,
        meter_type,
        meter_payment_type,
        tpr_count,
        valid_from,
        valid_to,
    ):
        self.description = description
        self.has_comms = has_comms
        self.is_hh = is_hh
        self.meter_type = meter_type
        self.meter_payment_type = meter_payment_type
        self.tpr_count = tpr_count
        self.valid_from = valid_from
        self.valid_to = valid_to

        if hh_after(valid_from, valid_to):
            raise BadRequest("The valid_from date can't be over the valid_to date.")

    @classmethod
    def insert(
        cls,
        sess,
        mtc,
        participant,
        description,
        has_comms,
        is_hh,
        meter_type,
        meter_payment_type,
        tpr_count,
        valid_from,
        valid_to,
    ):
        mtc_participant = cls(
            mtc,
            participant,
            description,
            has_comms,
            is_hh,
            meter_type,
            meter_payment_type,
            tpr_count,
            valid_from,
            valid_to,
        )
        sess.add(mtc_participant)
        sess.flush()
        return mtc_participant

    @staticmethod
    def find_by_values(sess, mtc, participant, date):
        q = select(MtcParticipant).where(
            MtcParticipant.mtc == mtc,
            MtcParticipant.participant == participant,
        )
        if date is None:
            q = q.where(MtcParticipant.valid_to == null())
        else:
            q = q.where(
                MtcParticipant.valid_from <= date,
                or_(MtcParticipant.valid_to == null(), MtcParticipant.valid_to >= date),
            )
        return sess.execute(q).scalar_one_or_none()

    @classmethod
    def get_by_values(cls, sess, mtc, participant, date):
        mtc_participant = cls.find_by_values(sess, mtc, participant, date)
        if mtc_participant is None:
            raise BadRequest(
                f"There isn't an MTC Participant with the MTC {mtc} and participant "
                f"{participant} at date {hh_format(date)}."
            )
        return mtc_participant


class MtcLlfc(Base, PersistentClass):
    __tablename__ = "mtc_llfc"
    id = Column(Integer, primary_key=True)
    mtc_participant_id = Column(Integer, ForeignKey("mtc_participant.id"), index=True)
    llfc_id = Column(Integer, ForeignKey("llfc.id"), index=True)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("mtc_participant_id", "llfc_id", "valid_from"),)

    def __init__(
        self,
        mtc_participant,
        llfc,
        valid_from,
        valid_to,
    ):
        self.mtc_participant = mtc_participant
        self.llfc = llfc
        self.valid_from = valid_from
        self.update(
            valid_to,
        )

    def update(
        self,
        valid_to,
    ):
        self.valid_to = valid_to

        if hh_after(self.valid_from, valid_to):
            raise BadRequest("The valid_from date can't be after the valid_to date.")

    @classmethod
    def insert(
        cls,
        sess,
        mtc_participant,
        llfc,
        valid_from,
        valid_to,
    ):
        if mtc_participant.participant.code != llfc.dno.participant.code:
            raise Exception(
                f"The MTC Participant {mtc_participant.participant.code} must match "
                f"the LLFC DNO Participant {llfc.dno.participant.code}"
            )
        mtc_llfc = cls(
            mtc_participant,
            llfc,
            valid_from,
            valid_to,
        )
        sess.add(mtc_llfc)
        sess.flush()
        return mtc_llfc

    @staticmethod
    def find_by_values(sess, mtc_participant, llfc, date):
        q = select(MtcLlfc).where(
            MtcLlfc.mtc_participant == mtc_participant,
            MtcLlfc.llfc == llfc,
        )
        if date is None:
            q = q.where(MtcLlfc.valid_to == null())
        else:
            q = q.where(
                MtcLlfc.valid_from <= date,
                or_(MtcLlfc.valid_to == null(), MtcLlfc.valid_to >= date),
            )
        return sess.execute(q).scalar_one_or_none()

    @classmethod
    def get_by_values(cls, sess, mtc_participant, llfc, date):
        mtc_llfc = cls.find_by_values(sess, mtc_participant, llfc, date)
        if mtc_llfc is None:
            raise BadRequest(
                f"There isn't an MTC LLFC with the MTC Participant "
                f"{mtc_participant.mtc.code} "
                f"{hh_format(mtc_participant.mtc.valid_from)} "
                f"{mtc_participant.participant.code} and LLFC {llfc.code} "
                f"{hh_format(llfc.valid_from)} at date {hh_format(date)}."
            )
        return mtc_llfc


class MtcSsc(Base, PersistentClass):
    __tablename__ = "mtc_ssc"
    id = Column(Integer, primary_key=True)
    mtc_participant_id = Column(Integer, ForeignKey("mtc_participant.id"), index=True)
    ssc_id = Column(Integer, ForeignKey("ssc.id"), index=True)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    mtc_llfc_sscs = relationship("MtcLlfcSsc", backref="mtc_ssc")
    __table_args__ = (UniqueConstraint("mtc_participant_id", "ssc_id", "valid_from"),)

    def __init__(self, mtc_participant, ssc, valid_from, valid_to):
        self.mtc_participant = mtc_participant
        self.ssc = ssc
        self.valid_from = valid_from
        self.update(valid_to)

    def update(self, valid_to):
        self.valid_to = valid_to

        if hh_after(self.valid_from, valid_to):
            raise BadRequest("The valid_from date can't be after the valid_to date.")

    @classmethod
    def insert(cls, sess, mtc_participant, ssc, valid_from, valid_to):
        mtc_ssc = cls(mtc_participant, ssc, valid_from, valid_to)
        sess.add(mtc_ssc)
        sess.flush()
        return mtc_ssc

    @staticmethod
    def find_by_values(sess, mtc_participant, ssc, date):
        q = select(MtcSsc).where(
            MtcSsc.mtc_participant == mtc_participant,
            MtcSsc.ssc == ssc,
        )
        if date is None:
            q = q.where(MtcSsc.valid_to == null())
        else:
            q = q.where(
                MtcSsc.valid_from <= date,
                or_(MtcSsc.valid_to == null(), MtcSsc.valid_to >= date),
            )
        return sess.execute(q).scalar_one_or_none()

    @classmethod
    def get_by_values(cls, sess, mtc_participant, ssc, date):
        mtc_ssc = cls.find_by_values(sess, mtc_participant, ssc, date)
        if mtc_ssc is None:
            raise BadRequest(
                f"For the participant {mtc_participant.participant.code} there isn't "
                f"an MTC SSC with the MTC {mtc_participant.mtc.code} and SSC "
                f"{ssc.code} at date {hh_format(date)}."
            )
        return mtc_ssc


class MtcLlfcSsc(Base, PersistentClass):
    __tablename__ = "mtc_llfc_ssc"
    id = Column(Integer, primary_key=True)
    mtc_ssc_id = Column(Integer, ForeignKey("mtc_ssc.id"), index=True)
    llfc_id = Column(Integer, ForeignKey("llfc.id"), index=True)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    mtc_llfc_ssc_pcs = relationship("MtcLlfcSscPc", backref="mtc_llfc_ssc")
    __table_args__ = (UniqueConstraint("mtc_ssc_id", "llfc_id", "valid_from"),)

    def __init__(self, mtc_ssc, llfc, valid_from, valid_to):
        self.mtc_ssc = mtc_ssc
        self.llfc = llfc
        self.valid_from = valid_from
        self.update(valid_to)

    def update(self, valid_to):
        self.valid_to = valid_to

        if hh_after(self.valid_from, valid_to):
            raise BadRequest("The valid_from date can't be after the valid_to date.")

    @classmethod
    def insert(cls, sess, mtc_ssc, llfc, valid_from, valid_to):
        mtc_llfc_ssc = cls(mtc_ssc, llfc, valid_from, valid_to)
        sess.add(mtc_llfc_ssc)
        sess.flush()
        return mtc_llfc_ssc

    @staticmethod
    def find_by_values(sess, mtc_ssc, llfc, date):
        q = select(MtcLlfcSsc).where(
            MtcLlfcSsc.mtc_ssc == mtc_ssc,
            MtcLlfcSsc.llfc == llfc,
        )
        if date is None:
            q = q.where(MtcLlfcSsc.valid_to == null())
        else:
            q = q.where(
                MtcLlfcSsc.valid_from <= date,
                or_(MtcLlfcSsc.valid_to == null(), MtcLlfcSsc.valid_to >= date),
            )
        return sess.execute(q).scalar_one_or_none()

    @classmethod
    def get_by_values(cls, sess, mtc_ssc, llfc, date):
        mtc_llfc_ssc = cls.find_by_values(sess, mtc_ssc, llfc, date)
        if mtc_llfc_ssc is None:
            raise BadRequest(
                f"There isn't an MTC LLFC SSC with the MTC Participant "
                f"{mtc_ssc.mtc_participant.mtc.code} "
                f"{hh_format(mtc_ssc.mtc_participant.mtc.valid_from)} "
                f"{mtc_ssc.mtc_participant.participant.code} "
                f"{hh_format(mtc_ssc.mtc_participant.valid_from)} LLFC {llfc.code} "
                f"{hh_format(llfc.valid_from)} SSC {mtc_ssc.ssc.code} "
                f"{hh_format(mtc_ssc.ssc.valid_from)} date {hh_format(date)}."
            )
        return mtc_llfc_ssc


class Tpr(Base, PersistentClass):
    __tablename__ = "tpr"
    id = Column(BigInteger, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    is_teleswitch = Column(Boolean, nullable=False)
    is_gmt = Column(Boolean, nullable=False)
    clock_intervals = relationship("ClockInterval", backref="tpr")
    measurement_requirements = relationship("MeasurementRequirement", backref="tpr")
    register_reads = relationship("RegisterRead", backref="tpr")

    def __init__(self, code, is_teleswitch, is_gmt):
        self.code = code.zfill(5)
        self.is_teleswitch = is_teleswitch
        self.is_gmt = is_gmt

    def insert_clock_interval(
        self,
        sess,
        day_of_week,
        start_day,
        start_month,
        end_day,
        end_month,
        start_hour,
        start_minute,
        end_hour,
        end_minute,
    ):
        ci = ClockInterval(
            self,
            day_of_week,
            start_day,
            start_month,
            end_day,
            end_month,
            start_hour,
            start_minute,
            end_hour,
            end_minute,
        )
        sess.add(ci)
        sess.flush()
        return ci

    @classmethod
    def insert(cls, sess, code, is_teleswitch, is_gmt):
        tpr = cls(code, is_teleswitch, is_gmt)
        sess.add(tpr)
        sess.flush()
        return tpr

    @staticmethod
    def find_by_code(sess, code):
        full_code = Tpr.normalise_code(code)
        return sess.execute(
            select(Tpr).where(Tpr.code == full_code)
        ).scalar_one_or_none()

    @staticmethod
    def get_by_code(sess, code):
        full_code = Tpr.normalise_code(code)
        tpr = sess.execute(
            select(Tpr).where(Tpr.code == full_code)
        ).scalar_one_or_none()
        if tpr is None:
            raise BadRequest(
                f"A TPR with code '{code}' expanded to '{full_code}' can't be found."
            )
        return tpr

    @staticmethod
    def normalise_code(code):
        return code.zfill(5)


class ClockInterval(Base, PersistentClass):
    __tablename__ = "clock_interval"
    id = Column(Integer, primary_key=True)
    tpr_id = Column(Integer, ForeignKey("tpr.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_day = Column(Integer, nullable=False)
    start_month = Column(Integer, nullable=False)
    end_day = Column(Integer, nullable=False)
    end_month = Column(Integer, nullable=False)
    start_hour = Column(Integer, nullable=False)
    start_minute = Column(Integer, nullable=False)
    end_hour = Column(Integer, nullable=False)
    end_minute = Column(Integer, nullable=False)

    def __init__(
        self,
        tpr,
        day_of_week,
        start_day,
        start_month,
        end_day,
        end_month,
        start_hour,
        start_minute,
        end_hour,
        end_minute,
    ):
        self.tpr = tpr
        self.day_of_week = day_of_week
        self.start_day = start_day
        self.start_month = start_month
        self.end_day = end_day
        self.end_month = end_month
        self.start_hour = start_hour
        self.start_minute = start_minute
        self.end_hour = end_hour
        self.end_minute = end_minute


class MeasurementRequirement(Base, PersistentClass):
    __tablename__ = "measurement_requirement"
    id = Column(Integer, primary_key=True)
    ssc_id = Column(Integer, ForeignKey("ssc.id"), nullable=False)
    tpr_id = Column(Integer, ForeignKey("tpr.id"), nullable=False)
    __table_args__ = (UniqueConstraint("ssc_id", "tpr_id"),)

    def __init__(self, ssc, tpr):
        self.ssc = ssc
        self.tpr = tpr

    @classmethod
    def insert(cls, sess, ssc, tpr):
        mr = cls(ssc, tpr)
        sess.add(mr)
        sess.flush()
        return mr


class Ssc(Base, PersistentClass):
    __tablename__ = "ssc"
    id = Column(BigInteger, primary_key=True)
    code = Column(String, nullable=False)
    description = Column(String)
    is_import = Column(Boolean)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    measurement_requirements = relationship("MeasurementRequirement", backref="ssc")
    eras = relationship("Era", backref="ssc")
    mtc_sscs = relationship("MtcSsc", backref="ssc")
    __table_args__ = (UniqueConstraint("code", "valid_from"),)

    def __init__(self, code, description, is_import, valid_from, valid_to):
        self.code = code
        self.description = description
        self.is_import = is_import
        self.valid_from = valid_from
        self.valid_to = valid_to

    @classmethod
    def insert(cls, sess, code, description, is_import, valid_from, valid_to):
        ssc = cls(code, description, is_import, valid_from, valid_to)
        sess.add(ssc)
        sess.flush()
        return ssc

    @staticmethod
    def find_by_code(sess, code, date):
        code = Ssc.normalise_code(code)
        q = select(Ssc).where(Ssc.code == code)
        if date is None:
            q = q.where(Ssc.valid_to == null())
        else:
            q = q.where(
                Ssc.valid_from <= date,
                or_(Ssc.valid_to == null(), Ssc.valid_to >= date),
            )
        return sess.execute(q).scalar_one_or_none()

    @classmethod
    def get_by_code(cls, sess, code, date):
        ssc = cls.find_by_code(sess, code, date)
        if ssc is None:
            raise BadRequest(
                f"The SSC with code '{code}' can't be found at {hh_format(date)}."
            )
        return ssc

    @staticmethod
    def normalise_code(code):
        return code.strip().zfill(4)


class MtcLlfcSscPc(Base, PersistentClass):
    __tablename__ = "mtc_llfc_ssc_pc"
    id = Column(BigInteger, primary_key=True)
    mtc_llfc_ssc_id = Column(BigInteger, ForeignKey("mtc_llfc_ssc.id"), nullable=False)
    pc_id = Column(BigInteger, ForeignKey("pc.id"), nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("mtc_llfc_ssc_id", "pc_id", "valid_from"),)

    def __init__(self, mtc_llfc_ssc, pc, valid_from, valid_to):
        self.mtc_llfc_ssc = mtc_llfc_ssc
        self.pc = pc
        self.valid_from = valid_from
        self.update(valid_to)

    def update(self, valid_to):
        self.valid_to = valid_to

    @classmethod
    def insert(cls, sess, mtc_llfc_ssc, pc, valid_from, valid_to):
        combo = cls(mtc_llfc_ssc, pc, valid_from, valid_to)
        sess.add(combo)
        sess.flush()
        return combo

    @staticmethod
    def find_by_values(sess, mtc_llfc_ssc, pc, date):
        q = select(MtcLlfcSscPc).where(
            MtcLlfcSscPc.mtc_llfc_ssc == mtc_llfc_ssc,
            MtcLlfcSscPc.pc == pc,
        )
        if date is None:
            q = q.where(MtcLlfcSscPc.valid_to == null())
        else:
            q = q.where(
                MtcLlfcSscPc.valid_from <= date,
                or_(
                    MtcLlfcSscPc.valid_to == null(),
                    MtcLlfcSscPc.valid_to >= date,
                ),
            )
        return sess.execute(q).scalar_one_or_none()

    @classmethod
    def get_by_values(cls, sess, mtc_llfc_ssc, pc, date):
        combo = cls.find_by_values(sess, mtc_llfc_ssc, pc, date)
        if combo is None:
            raise BadRequest(
                f"The valid combination of MTC LLFC SSC {mtc_llfc_ssc.id} and PC "
                f"{pc.code} at {hh_format(date)} can't be found."
            )
        return combo


class SiteEra(Base, PersistentClass):
    __tablename__ = "site_era"
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("site.id"))
    era_id = Column(Integer, ForeignKey("era.id"))
    is_physical = Column(Boolean, nullable=False)

    def __init__(self, site, era, is_physical):
        self.site = site
        self.era = era
        self.is_physical = is_physical


class EnergisationStatus(Base, PersistentClass):
    __tablename__ = "energisation_status"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    eras = relationship("Era", backref="energisation_status")

    def __init__(self, code, description):
        self.code = code
        self.description = description

    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        es = sess.query(EnergisationStatus).filter_by(code=code).first()
        if es is None:
            raise BadRequest(
                f"The Energisation Status with code {code} can't be found."
            )
        return es

    @staticmethod
    def insert(sess, code, description):
        energisation_status = EnergisationStatus(code, description)
        sess.add(energisation_status)
        sess.flush()
        return energisation_status


class Era(Base, PersistentClass):
    __tablename__ = "era"
    id = Column(Integer, primary_key=True)
    supply_id = Column(Integer, ForeignKey("supply.id"), nullable=False)
    site_eras = relationship("SiteEra", backref="era")
    start_date = Column(DateTime(timezone=True), nullable=False)
    finish_date = Column(DateTime(timezone=True))
    mop_contract_id = Column(Integer, ForeignKey("contract.id"), nullable=False)
    mop_contract = relationship(
        "Contract", primaryjoin="Contract.id==Era.mop_contract_id"
    )
    mop_account = Column(String, nullable=False)
    dc_contract_id = Column(Integer, ForeignKey("contract.id"), nullable=False)
    dc_contract = relationship(
        "Contract", primaryjoin="Contract.id==Era.dc_contract_id"
    )
    dc_account = Column(String)
    msn = Column(String)
    pc_id = Column(Integer, ForeignKey("pc.id"), nullable=False)
    mtc_participant_id = Column(
        Integer, ForeignKey("mtc_participant.id"), nullable=False
    )
    cop_id = Column(Integer, ForeignKey("cop.id"), nullable=False)
    comm_id = Column(Integer, ForeignKey("comm.id"), nullable=False)
    ssc_id = Column(Integer, ForeignKey("ssc.id"))
    energisation_status_id = Column(
        Integer, ForeignKey("energisation_status.id"), nullable=False
    )
    dtc_meter_type_id = Column(Integer, ForeignKey("dtc_meter_type.id"))
    imp_mpan_core = Column(String)
    imp_llfc_id = Column(Integer, ForeignKey("llfc.id"))
    imp_llfc = relationship("Llfc", primaryjoin="Llfc.id==Era.imp_llfc_id")
    imp_supplier_contract_id = Column(Integer, ForeignKey("contract.id"))
    imp_supplier_contract = relationship(
        "Contract", primaryjoin="Contract.id==Era.imp_supplier_contract_id"
    )
    imp_supplier_account = Column(String)
    imp_sc = Column(Integer)
    exp_mpan_core = Column(String)
    exp_llfc_id = Column(Integer, ForeignKey("llfc.id"))
    exp_llfc = relationship("Llfc", primaryjoin="Llfc.id==Era.exp_llfc_id")
    exp_supplier_contract_id = Column(Integer, ForeignKey("contract.id"))
    exp_supplier_contract = relationship(
        "Contract", primaryjoin="Contract.id==Era.exp_supplier_contract_id"
    )
    exp_supplier_account = Column(String)
    exp_sc = Column(Integer)
    channels = relationship("Channel", backref="era")

    def __init__(
        self,
        sess,
        supply,
        start_date,
        finish_date,
        mop_contract,
        mop_account,
        dc_contract,
        dc_account,
        msn,
        pc,
        mtc_code,
        cop,
        comm,
        ssc_code,
        energisation_status,
        properties,
        imp_mpan_core,
        imp_llfc_code,
        imp_supplier_contract,
        imp_supplier_account,
        imp_sc,
        exp_mpan_core,
        exp_llfc_code,
        exp_supplier_contract,
        exp_supplier_account,
        exp_sc,
    ):
        self.supply = supply
        self.update(
            sess,
            start_date,
            finish_date,
            mop_contract,
            mop_account,
            dc_contract,
            dc_account,
            msn,
            pc,
            mtc_code,
            cop,
            comm,
            ssc_code,
            energisation_status,
            properties,
            imp_mpan_core,
            imp_llfc_code,
            imp_supplier_contract,
            imp_supplier_account,
            imp_sc,
            exp_mpan_core,
            exp_llfc_code,
            exp_supplier_contract,
            exp_supplier_account,
            exp_sc,
        )

    def attach_site(self, sess, site, is_location=False):
        if site in sess.query(Site).join(SiteEra).filter(SiteEra.era == self).all():
            raise BadRequest("The site is already attached to this supply.")

        site_era = SiteEra(site, self, False)
        sess.add(site_era)
        sess.flush()
        if is_location:
            self.set_physical_location(sess, site)

    def detach_site(self, sess, site):
        site_era = (
            sess.query(SiteEra)
            .filter(SiteEra.era == self, SiteEra.site == site)
            .first()
        )
        if site_era is None:
            raise BadRequest(
                "Can't detach this era from this site, as it isn't attached."
            )
        if site_era.is_physical:
            raise BadRequest(
                "You can't detach an era from the site where it is physically located."
            )

        sess.delete(site_era)
        sess.flush()

    def find_channel(self, sess, imp_related, channel_type):
        return (
            sess.query(Channel)
            .filter(
                Channel.era == self,
                Channel.imp_related == imp_related,
                Channel.channel_type == channel_type,
            )
            .first()
        )

    def get_channel(self, sess, imp_related, channel_type):
        chan = self.find_channel(sess, imp_related, channel_type)
        if chan is None:
            return BadRequest("Can't find the channel.")
        return chan

    def update_dates(self, sess, start_date, finish_date):
        if start_date == self.start_date and finish_date == self.finish_date:
            return
        else:
            self.update(
                sess,
                start_date,
                finish_date,
                self.mop_contract,
                self.mop_account,
                self.dc_contract,
                self.dc_account,
                self.msn,
                self.pc,
                self.mtc_participant.mtc.code,
                self.cop,
                self.comm,
                None if self.ssc is None else self.ssc.code,
                self.energisation_status,
                self.dtc_meter_type,
                self.imp_mpan_core,
                None if self.imp_llfc is None else self.imp_llfc.code,
                self.imp_supplier_contract,
                self.imp_supplier_account,
                self.imp_sc,
                self.exp_mpan_core,
                None if self.exp_llfc is None else self.exp_llfc.code,
                self.exp_supplier_contract,
                self.exp_supplier_account,
                self.exp_sc,
            )

    def update(
        self,
        sess,
        start_date,
        finish_date,
        mop_contract,
        mop_account,
        dc_contract,
        dc_account,
        msn,
        pc,
        mtc_code,
        cop,
        comm,
        ssc_code,
        energisation_status,
        dtc_meter_type,
        imp_mpan_core,
        imp_llfc_code,
        imp_supplier_contract,
        imp_supplier_account,
        imp_sc,
        exp_mpan_core,
        exp_llfc_code,
        exp_supplier_contract,
        exp_supplier_account,
        exp_sc,
    ):
        orig_start_date = self.start_date
        orig_finish_date = self.finish_date

        if hh_after(start_date, finish_date):
            raise BadRequest("The era start date can't be after the finish date.")

        if imp_mpan_core is None and exp_mpan_core is None:
            raise BadRequest("An era must have at least one MPAN.")

        if mop_contract is None:
            raise BadRequest("An supply era must have a MOP contract.")

        mop_account = mop_account.strip()
        if len(mop_account) == 0:
            raise BadRequest("There must be a MOP account reference.")

        if dc_contract is None:
            raise BadRequest("An era must have a DC contract.")

        dc_account = dc_account.strip()
        if len(dc_account) == 0:
            raise BadRequest("An era must have a DC account reference.")

        self.msn = msn.strip()
        self.pc = pc
        self.ssc = (
            None if ssc_code is None else Ssc.get_by_code(sess, ssc_code, start_date)
        )

        if pc.code == "00" and self.ssc is not None:
            raise BadRequest(
                "A supply with Profile Class 00 can't have a Standard Settlement "
                "Configuration."
            )
        if pc.code != "00" and self.ssc is None:
            raise BadRequest(
                "A NHH supply must have a Standard Settlement Configuration."
            )
        self.energisation_status = energisation_status
        self.dtc_meter_type = dtc_meter_type

        locs = locals()
        voltage_level = None
        self.cop = cop
        self.comm = comm

        mtc = Mtc.get_by_code(sess, mtc_code, start_date)
        self.mtc_participant = MtcParticipant.get_by_values(
            sess, mtc, self.supply.dno.participant, start_date
        )

        self.start_date = start_date
        self.finish_date = finish_date
        self.mop_account = mop_account
        self.mop_contract = mop_contract
        self.dc_account = dc_account
        self.dc_contract = dc_contract

        for polarity in ["imp", "exp"]:
            mcore_str = locs[polarity + "_mpan_core"]
            if mcore_str is None:
                for suf in [
                    "mpan_core",
                    "llfc",
                    "supplier_contract",
                    "supplier_account",
                    "sc",
                ]:
                    setattr(self, polarity + "_" + suf, None)
                continue

            mcore = parse_mpan_core(mcore_str)

            if mcore[:2] != self.supply.dno.dno_code:
                raise BadRequest(
                    f"The DNO code of the MPAN core {mcore} doesn't match the DNO "
                    f"code of the supply."
                )

            setattr(self, polarity + "_mpan_core", mcore)

            supplier_contract = locs[polarity + "_supplier_contract"]
            if supplier_contract is None:
                raise BadRequest(
                    f"There's an {polarity} MPAN core, but no {polarity} supplier "
                    f"contract."
                )
            if supplier_contract.start_date() > start_date:
                raise BadRequest(
                    f"For the era {self.id} the {polarity} supplier contract "
                    f"{supplier_contract.id} starts at "
                    f"{hh_format(supplier_contract.start_date())} which is after "
                    f"the start of the era at {hh_format(start_date)}."
                )

            if hh_before(supplier_contract.finish_date(), finish_date):
                raise BadRequest("The supplier contract finishes before the era.")
            supplier_account = locs[polarity + "_supplier_account"]
            setattr(self, f"{polarity}_supplier_contract", supplier_contract)
            setattr(self, f"{polarity}_supplier_account", supplier_account)

            llfc_code = locs[f"{polarity}_llfc_code"]
            llfc = self.supply.dno.get_llfc_by_code(sess, llfc_code, start_date)
            if finish_date is not None and hh_before(llfc.valid_to, finish_date):
                raise BadRequest(
                    f"The {polarity} line loss factor {llfc_code} is only valid "
                    f"until {hh_format(llfc.valid_to)} but the era ends at "
                    f"{hh_format(finish_date)}."
                )

            if llfc.is_import != ("imp" == polarity):
                raise BadRequest(
                    f"The {polarity} line loss factor {llfc.code} is actually "
                    "an " + ("imp" if llfc.is_import else "exp") + " one."
                )
            vl = llfc.voltage_level
            if voltage_level is None:
                voltage_level = vl
            elif voltage_level != vl:
                raise BadRequest(
                    "The voltage level indicated by the Line Loss Factor "
                    "must be the same for both the MPANs."
                )
            setattr(self, polarity + "_llfc", llfc)
            sc = locs[polarity + "_sc"]
            if sc is None:
                raise BadRequest(
                    f"There's an {polarity} MPAN core, but no {polarity} Supply "
                    f"Capacity."
                )

            setattr(self, polarity + "_sc", sc)

            if self.supply.dno.dno_code not in ("99", "88"):
                if pc.code == "00":
                    mtc_llfc = MtcLlfc.get_by_values(
                        sess, self.mtc_participant, llfc, start_date
                    )
                    if finish_date is not None and hh_before(
                        mtc_llfc.valid_to, finish_date
                    ):
                        raise BadRequest(
                            f"The {polarity} combination of MTC "
                            f"{self.mtc_participant.mtc.code} LLFC {llfc.code} is "
                            f"only valid until {hh_format(mtc_llfc.valid_to)} but "
                            f"the era ends at {hh_format(finish_date)}."
                        )
                else:
                    mtc_ssc = MtcSsc.get_by_values(
                        sess, self.mtc_participant, self.ssc, start_date
                    )
                    mtc_llfc_ssc = MtcLlfcSsc.get_by_values(
                        sess, mtc_ssc, llfc, start_date
                    )
                    combo = MtcLlfcSscPc.get_by_values(
                        sess, mtc_llfc_ssc, pc, start_date
                    )
                    if finish_date is not None and hh_before(
                        combo.valid_to, finish_date
                    ):
                        raise BadRequest(
                            f"The {polarity} combination of MTC "
                            f"{self.mtc_participant.mtc.code} LLFC {llfc.code} SSC "
                            f"{self.ssc.code} PC {pc.code} is only valid until "
                            f"{hh_format(combo.valid_to)} but the era ends at "
                            f"{hh_format(finish_date)}."
                        )

        if cop.code not in [
            c.code for c in Cop.get_valid(sess, self.mtc_participant.meter_type)
        ]:
            raise BadRequest(
                f"The CoP of {cop.code} is not compatible with the meter type code "
                f"of {self.mtc_participant.meter_type.code}."
            )

        if dc_contract.start_date() > start_date:
            raise BadRequest("The DC contract starts after the era.")

        if hh_before(dc_contract.finish_date(), finish_date):
            raise BadRequest(
                f"The DC contract {dc_contract.id} finishes before the era."
            )

        if mop_contract.start_date() > start_date:
            raise BadRequest("The MOP contract starts after the supply era.")

        if hh_before(mop_contract.finish_date(), finish_date):
            raise BadRequest(
                f"The MOP contract {mop_contract.id} finishes before the era."
            )

        prev_era = self.supply.find_era_at(sess, prev_hh(orig_start_date))
        next_era = self.supply.find_era_at(sess, next_hh(orig_finish_date))

        if prev_era is not None:
            is_overlap = False
            if imp_mpan_core is not None:
                prev_imp_mpan_core = prev_era.imp_mpan_core
                if (
                    prev_imp_mpan_core is not None
                    and imp_mpan_core == prev_imp_mpan_core
                ):
                    is_overlap = True
            if not is_overlap and exp_mpan_core is not None:
                prev_exp_mpan_core = prev_era.exp_mpan_core
                if (
                    prev_exp_mpan_core is not None
                    and exp_mpan_core == prev_exp_mpan_core
                ):
                    is_overlap = True
            if not is_overlap:
                raise BadRequest(
                    "MPAN cores can't change without an overlapping period."
                )

        if next_era is not None:
            is_overlap = False
            if imp_mpan_core is not None:
                next_imp_mpan_core = next_era.imp_mpan_core
                if (
                    next_imp_mpan_core is not None
                    and imp_mpan_core == next_imp_mpan_core
                ):
                    is_overlap = True
            if not is_overlap and exp_mpan_core is not None:
                next_exp_mpan_core = next_era.exp_mpan_core
                if (
                    next_exp_mpan_core is not None
                    and exp_mpan_core == next_exp_mpan_core
                ):
                    is_overlap = True
            if not is_overlap:
                raise BadRequest(
                    "MPAN cores can't change without an overlapping period."
                )

    def insert_channel(self, sess, imp_related, channel_type):
        channel = Channel(self, imp_related, channel_type)
        try:
            sess.add(channel)
            sess.flush()
        except SQLAlchemyError as e:
            sess.rollback()
            raise BadRequest(
                f"There's already a channel with import related: {imp_related} and "
                f"channel type: {channel_type}. {e}"
            )

        channel.add_snag(sess, Snag.MISSING, self.start_date, self.finish_date)
        return channel

    def set_physical_location(self, sess, site):
        target_ssgen = (
            sess.query(SiteEra)
            .filter(SiteEra.era == self, SiteEra.site == site)
            .first()
        )
        if target_ssgen is None:
            raise BadRequest("The site isn't attached to this supply.")

        for ssgen in self.site_eras:
            ssgen.is_physical = ssgen == target_ssgen
        sess.flush()

    def delete_channel(self, sess, imp_related, channel_type):
        channel = self.get_channel(sess, imp_related, channel_type)
        if sess.query(HhDatum).filter(HhDatum.channel == channel).count() > 0:
            raise BadRequest(
                "One can't delete a channel if there are still HH data attached to it."
            )

        for snag in sess.query(Snag).filter(Snag.channel == channel):
            sess.delete(snag)

        sess.delete(channel)
        sess.flush()

    @property
    def meter_category(self):
        if not hasattr(self, "_meter_category"):
            self._meter_category = METER_CATEGORY[
                None if self.dtc_meter_type is None else self.dtc_meter_type.code
            ]

        return self._meter_category

    def get_physical_site(self, sess):
        return sess.scalar(
            select(Site)
            .join(SiteEra)
            .where(SiteEra.era == self, SiteEra.is_physical == true())
        )


METER_CATEGORY = {
    None: "unmetered",
    "CHECK": "hh",
    "H": "hh",
    "K": "nhh",
    "LAG_": "hh",
    "LEAD_": "hh",
    "MAIN_": "hh",
    "N": "nhh",
    "NCAMR": "amr",
    "NSS": "amr",
    "RCAMR": "amr",
    "RCAMY": "amr",
    "S": "nhh",
    "S1": "amr",
    "S2A": "amr",
    "S2B": "amr",
    "S2C": "amr",
    "S2AD": "amr",
    "S2BD": "amr",
    "S2CDE": "amr",
    "SPECL": "nhh",
    "T": "nhh",
    "2ADF": "amr",
    "2ADEF": "amr",
    "2AEF": "amr",
    "2AF": "amr",
    "2BF": "amr",
    "2BDF": "amr",
    "2BDEF": "amr",
    "2BEF": "amr",
    "2CDEF": "amr",
    "2CF": "amr",
    "2CDF": "amr",
    "2CEF": "amr",
    "S2ADE": "amr",
    "S2BDE": "amr",
    "S2CD": "amr",
}


class Channel(Base, PersistentClass):
    __tablename__ = "channel"
    id = Column(Integer, primary_key=True)
    era_id = Column(Integer, ForeignKey("era.id"))
    imp_related = Column(Boolean, nullable=False)
    channel_type = Column(
        Enum("ACTIVE", "REACTIVE_IMP", "REACTIVE_EXP", name="channel_type"),
        nullable=False,
    )
    hh_data = relationship("HhDatum", backref="channel")
    snag = relationship("Snag", backref="channel")

    def __init__(self, era, imp_related, channel_type):
        self.era = era
        self.imp_related = imp_related
        self.channel_type = channel_type

    def add_snag(self, sess, description, start_date, finish_date):
        Snag.add_snag(sess, None, self, description, start_date, finish_date)

    def remove_snag(self, sess, description, start_date, finish_date):
        Snag.remove_snag(sess, None, self, description, start_date, finish_date)

    def delete_data(self, sess, start, finish):
        if start < self.era.start_date:
            raise BadRequest("The start date is before the beginning of the era.")
        if hh_after(finish, self.era.finish_date):
            raise BadRequest("The finish date is after the end of the era.")

        sess.execute(
            delete(HhDatum).where(
                HhDatum.channel == self,
                HhDatum.start_date >= start,
                HhDatum.start_date <= finish,
            )
        )

        self.add_snag(sess, Snag.MISSING, start, finish)

        if self.channel_type == "ACTIVE":
            site = self.era.get_physical_site(sess)
            site.hh_check(sess, start, finish)

    def add_hh_data(self, sess, data_raw):
        data = iter(
            sess.query(HhDatum.start_date, HhDatum.value, HhDatum.status)
            .filter(
                HhDatum.channel == self,
                HhDatum.start_date >= data_raw[0]["start_date"],
                HhDatum.start_date <= data_raw[-1]["start_date"],
            )
            .order_by(HhDatum.start_date)
        )

        datum_date, datum_value, datum_status = next(data, (None, None, None))

        insert_blocks, insert_date = [], None
        update_blocks, update_date = [], None
        upsert_blocks, upsert_date = [], None
        estimate_blocks, estimate_date = [], None
        negative_blocks, negative_date = [], None

        for datum_raw in data_raw:
            if datum_raw["start_date"] == datum_date:
                if (datum_value, datum_status) != (
                    datum_raw["value"],
                    datum_raw["status"],
                ):
                    if update_date != datum_raw["start_date"]:
                        update_block = []
                        update_blocks.append(update_block)
                    update_block.append(datum_raw)
                    update_date = datum_raw["start_date"] + HH
                    if upsert_date != datum_raw["start_date"]:
                        upsert_block = []
                        upsert_blocks.append(upsert_block)
                    upsert_block.append(datum_raw)
                    upsert_date = datum_raw["start_date"] + HH
                datum_date, datum_value, datum_status = next(data, (None, None, None))
            else:
                if datum_raw["start_date"] != insert_date:
                    insert_block = []
                    insert_blocks.append(insert_block)
                datum_raw["channel_id"] = self.id
                insert_block.append(datum_raw)
                insert_date = datum_raw["start_date"] + HH
                if upsert_date != datum_raw["start_date"]:
                    upsert_block = []
                    upsert_blocks.append(upsert_block)
                upsert_block.append(datum_raw)
                upsert_date = datum_raw["start_date"] + HH

            if upsert_date is not None and upsert_date > datum_raw["start_date"]:
                if datum_raw["status"] == "E":
                    if estimate_date != datum_raw["start_date"]:
                        estimate_block = []
                        estimate_blocks.append(estimate_block)
                    estimate_block.append(datum_raw)
                    estimate_date = datum_raw["start_date"] + HH
                if datum_raw["value"] < 0:
                    if negative_date != datum_raw["start_date"]:
                        negative_block = []
                        negative_blocks.append(negative_block)
                    negative_block.append(datum_raw)
                    negative_date = datum_raw["start_date"] + HH

        for b in insert_blocks:
            sess.execute(
                text(
                    "INSERT INTO hh_datum (channel_id, start_date, value, "
                    "status, last_modified) VALUES "
                    "(:channel_id, :start_date, :value, :status, "
                    "current_timestamp)"
                ),
                params=b,
            )
            sess.flush()
            self.remove_snag(
                sess, Snag.MISSING, b[0]["start_date"], b[-1]["start_date"]
            )
            sess.flush()

        for block in update_blocks:
            start_date = block[0]["start_date"]
            finish_date = block[-1]["start_date"]
            for dw in block:
                sess.execute(
                    text(
                        "update hh_datum set value = :value, status = :status, "
                        "last_modified = current_timestamp "
                        "where channel_id = :channel_id and "
                        "start_date = :start_date"
                    ),
                    params={
                        "value": dw["value"],
                        "status": dw["status"],
                        "channel_id": self.id,
                        "start_date": dw["start_date"],
                    },
                )
            self.remove_snag(sess, Snag.NEGATIVE, start_date, finish_date)
            self.remove_snag(sess, Snag.ESTIMATED, start_date, finish_date)
            sess.flush()

        if self.channel_type == "ACTIVE":
            site = (
                sess.query(Site)
                .join(SiteEra)
                .filter(SiteEra.era == self.era, SiteEra.is_physical == true())
                .one()
            )
            for b in upsert_blocks:
                site.hh_check(sess, b[0]["start_date"], b[-1]["start_date"])
                sess.flush()

        for b in negative_blocks:
            self.add_snag(sess, Snag.NEGATIVE, b[0]["start_date"], b[-1]["start_date"])
            sess.flush()

        for b in estimate_blocks:
            self.add_snag(sess, Snag.ESTIMATED, b[0]["start_date"], b[-1]["start_date"])
            sess.flush()

        sess.commit()
        sess.flush()


class HhDatum(Base, PersistentClass):
    # status A actual, E estimated, C padding
    @staticmethod
    def insert(sess, raw_data, contract=None):
        mpan_core = channel_type = prev_date = era_finish_date = channel = None
        data = []
        for datum in raw_data:
            if (
                len(data) > 1000
                or not (
                    mpan_core == datum["mpan_core"]
                    and datum["channel_type"] == channel_type
                    and datum["start_date"] == prev_date + HH
                )
                or (
                    era_finish_date is not None
                    and era_finish_date < datum["start_date"]
                )
            ):
                if len(data) > 0:
                    channel.add_hh_data(sess, data)
                    data = []
                mpan_core = datum["mpan_core"]
                channel_type = datum["channel_type"]
                channel_q = (
                    sess.query(Channel)
                    .join(Era)
                    .filter(
                        Channel.channel_type == channel_type,
                        Era.start_date <= datum["start_date"],
                        or_(
                            Era.finish_date == null(),
                            Era.finish_date >= datum["start_date"],
                        ),
                        or_(
                            and_(
                                Era.imp_mpan_core == mpan_core,
                                Channel.imp_related == true(),
                            ),
                            and_(
                                Era.exp_mpan_core == mpan_core,
                                Channel.imp_related == false(),
                            ),
                        ),
                    )
                    .options(joinedload(Channel.era))
                )

                if contract is not None:
                    channel_q = channel_q.filter(Era.dc_contract == contract)

                channel = channel_q.first()

                if channel is None:
                    datum_str = ", ".join(
                        [
                            mpan_core,
                            hh_format(datum["start_date"]),
                            channel_type,
                            str(datum["value"]),
                            datum["status"],
                        ]
                    )
                    if contract is None:
                        msg = f"There is no channel for the datum ({datum_str})."
                    else:
                        msg = (
                            f"There is no channel under the contract {contract.name} "
                            f"for the datum ({datum_str})."
                        )
                    raise BadRequest(msg)

                era_finish_date = channel.era.finish_date
            prev_date = datum["start_date"]
            data.append(datum)
        if len(data) > 0:
            channel.add_hh_data(sess, data)

    __tablename__ = "hh_datum"
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channel.id"))
    start_date = Column(DateTime(timezone=True), nullable=False)
    value = Column(Numeric, nullable=False)
    status = Column(String, nullable=False)
    last_modified = Column(DateTime(timezone=True), nullable=False)
    __table_args__ = (UniqueConstraint("channel_id", "start_date"),)

    def __init__(self, channel, datum_raw):
        self.channel = channel
        self.start_date = datum_raw["start_date"]
        self.update(datum_raw["value"], datum_raw["status"])

    def __str__(self):
        buf = []
        for prop in ("status", "start_date", "channel_type", "value", "mpan_core"):
            buf.append("'" + prop + "': '" + str(getattr(self, prop)) + "'")
        return "{" + ", ".join(buf) + "}"

    def update(self, value, status):
        if status not in ("E", "A", "C"):
            raise BadRequest("The status character must be E, A or C.")

        self.value = value
        self.status = status
        nw = utc_datetime_now()
        self.last_modified = utc_datetime(year=nw.year, month=nw.month, day=nw.day)


class Supply(Base, PersistentClass):
    @staticmethod
    def get_by_mpan_core(sess, mpan_core):
        supply = Supply.find_by_mpan_core(sess, mpan_core)
        if supply is None:
            raise BadRequest(f"The MPAN core {mpan_core} is not set up in Chellow.")
        return supply

    @staticmethod
    def find_by_mpan_core(sess, mpan_core):
        if mpan_core is None:
            return None
        else:
            return (
                sess.query(Supply)
                .join(Era)
                .distinct()
                .filter(
                    or_(Era.imp_mpan_core == mpan_core, Era.exp_mpan_core == mpan_core)
                )
                .first()
            )

    @staticmethod
    def _settle_stripe(sess, start_date, finish_date, old_era, new_era):
        # move snags from old to new
        if old_era is None:
            for channel in (
                sess.query(Channel).filter(Channel.era == new_era).order_by(Channel.id)
            ):
                channel.add_snag(sess, Snag.MISSING, start_date, finish_date)

        if new_era is None:
            for channel in (
                sess.query(Channel).filter(Channel.era == old_era).order_by(Channel.id)
            ):
                for desc in [Snag.MISSING, Snag.NEGATIVE, Snag.ESTIMATED]:
                    channel.remove_snag(sess, desc, start_date, finish_date)

                hh_data = sess.query(HhDatum).filter(
                    HhDatum.channel == channel, HhDatum.start_date >= start_date
                )
                if finish_date is not None:
                    hh_data = hh_data.filter(HhDatum.start_date <= finish_date)
                if hh_data.count() > 0:
                    raise BadRequest(
                        f"There are orphaned HH data between {hh_format(start_date)} "
                        f"and {hh_format(finish_date)}."
                    )

        if old_era is not None and new_era is not None:
            for channel in (
                sess.query(Channel).filter(Channel.era == old_era).order_by(Channel.id)
            ):
                snags = (
                    sess.query(Snag)
                    .filter(
                        Snag.channel == channel,
                        or_(Snag.finish_date == null(), Snag.finish_date >= start_date),
                    )
                    .order_by(Snag.id)
                )
                if finish_date is not None:
                    snags = snags.filter(Snag.start_date <= finish_date)
                target_channel = new_era.find_channel(
                    sess, channel.imp_related, channel.channel_type
                )

                for snag in snags:
                    snag_start = max(snag.start_date, start_date)
                    snag_finish = (
                        snag.finish_date
                        if hh_before(snag.finish_date, finish_date)
                        else finish_date
                    )
                    if target_channel is not None:
                        target_channel.add_snag(
                            sess, snag.description, snag_start, snag_finish
                        )
                    channel.remove_snag(sess, snag.description, snag_start, snag_finish)

                hh_data = sess.query(HhDatum).filter(
                    HhDatum.channel == channel, HhDatum.start_date >= start_date
                )
                if finish_date is not None:
                    hh_data = hh_data.filter(HhDatum.start_date <= finish_date)

                if hh_data.count() > 0:
                    if target_channel is None:
                        raise BadRequest(
                            f"There is no channel for the import related: "
                            f"{channel.imp_related} and channel type: "
                            f"{channel.channel_type} HH data from "
                            f"{hh_format(start_date)} to move to in the era starting "
                            f"{hh_format(new_era.start_date)}, finishing "
                            f"{hh_format(new_era.finish_date)}."
                        )

                    q = (
                        update(HhDatum)
                        .where(
                            HhDatum.channel == channel, HhDatum.start_date >= start_date
                        )
                        .values({"channel_id": target_channel.id})
                    )
                    if finish_date is not None:
                        q = q.where(HhDatum.start_date <= finish_date)
                    sess.execute(q)

    __tablename__ = "supply"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    note = Column(Text, nullable=False)
    source_id = Column(Integer, ForeignKey("source.id"), nullable=False)
    generator_type_id = Column(Integer, ForeignKey("generator_type.id"))
    gsp_group_id = Column(Integer, ForeignKey("gsp_group.id"), nullable=False)
    dno_id = Column(Integer, ForeignKey("party.id"), nullable=False)
    eras = relationship("Era", backref="supply", order_by="Era.start_date")
    bills = relationship("Bill", backref="supply")

    def __init__(self, name, source, generator_type, gsp_group, dno):
        self.note = ""
        self.update(name, source, generator_type, gsp_group, dno)

    def update(self, name, source, generator_type, gsp_group, dno):
        if name is None:
            raise Exception("The supply name cannot be null.")

        name = name.strip()
        if len(name) == 0:
            raise BadRequest("The supply name can't be blank.")

        self.name = name
        self.source = source
        if source.code in ("gen", "gen-net") and generator_type is None:
            raise BadRequest(
                "If the source is 'gen' or 'gen-net', there must be a generator type."
            )

        if source.code == "net" and dno.dno_code == "99":
            raise BadRequest("A network supply can't have a DNO code  of 99.")

        if source.code in ("gen", "gen-net"):
            self.generator_type = generator_type
        else:
            self.generator_type = None

        self.gsp_group = gsp_group
        self.dno = dno

    def find_era_at(self, sess, dt):
        if dt is None:
            return (
                sess.query(Era)
                .filter(Era.supply == self, Era.finish_date == null())
                .first()
            )
        else:
            return (
                sess.query(Era)
                .filter(
                    Era.supply == self,
                    Era.start_date <= dt,
                    or_(Era.finish_date == null(), Era.finish_date >= dt),
                )
                .first()
            )

    def find_last_era(self, sess):
        return (
            sess.query(Era)
            .filter(Era.supply == self)
            .order_by(Era.start_date.desc())
            .first()
        )

    def find_eras(self, sess, start, finish):
        eras = (
            sess.query(Era)
            .filter(
                Era.supply == self,
                or_(Era.finish_date == null(), Era.finish_date >= start),
            )
            .order_by(Era.start_date)
        )
        if finish is not None:
            eras = eras.filter(Era.start_date <= finish)
        return eras.all()

    def update_era(
        self,
        sess,
        era,
        start_date,
        finish_date,
        mop_contract,
        mop_account,
        dc_contract,
        dc_account,
        msn,
        pc,
        mtc_code,
        cop,
        comm,
        ssc_code,
        energisation_status,
        properties,
        imp_mpan_core,
        imp_llfc_code,
        imp_supplier_contract,
        imp_supplier_account,
        imp_sc,
        exp_mpan_core,
        exp_llfc_code,
        exp_supplier_contract,
        exp_supplier_account,
        exp_sc,
    ):
        if era.supply != self:
            raise Exception("The era doesn't belong to this supply.")

        for mc in (imp_mpan_core, exp_mpan_core):
            if mc is not None:
                sup = (
                    sess.query(Era)
                    .filter(
                        Era.supply != self,
                        or_(Era.imp_mpan_core == mc, Era.exp_mpan_core == mc),
                    )
                    .first()
                )
                if sup is not None:
                    raise BadRequest(
                        f"The MPAN core {mc} is already attached to another supply."
                    )

        old_stripes = []
        new_stripes = []
        prev_era = self.find_era_at(sess, prev_hh(era.start_date))
        if prev_era is None:
            old_stripes.append(
                {
                    "start_date": utc_datetime(datetime.MINYEAR, 1, 2),
                    "finish_date": era.start_date - HH,
                    "era": None,
                }
            )
            new_stripes.append(
                {
                    "start_date": utc_datetime(datetime.MINYEAR, 1, 2),
                    "finish_date": start_date - HH,
                    "era": None,
                }
            )
        else:
            old_stripes.append(
                {
                    "start_date": prev_era.start_date,
                    "finish_date": prev_era.finish_date,
                    "era": prev_era,
                }
            )
            new_stripes.append(
                {
                    "start_date": prev_era.start_date,
                    "finish_date": start_date - HH,
                    "era": prev_era,
                }
            )

        if era.finish_date is None:
            next_era = None
        else:
            next_era = self.find_era_at(sess, next_hh(era.finish_date))

        if next_era is None:
            if era.finish_date is not None:
                old_stripes.append(
                    {
                        "start_date": era.finish_date + HH,
                        "finish_date": None,
                        "era": None,
                    }
                )
            if finish_date is not None:
                new_stripes.append(
                    {"start_date": finish_date + HH, "finish_date": None, "era": None}
                )
        else:
            old_stripes.append(
                {
                    "start_date": next_era.start_date,
                    "finish_date": next_era.finish_date,
                    "era": next_era,
                }
            )
            if finish_date is not None:
                new_stripes.append(
                    {
                        "start_date": finish_date + HH,
                        "finish_date": next_era.finish_date,
                        "era": next_era,
                    }
                )

        old_stripes.append(
            {"start_date": era.start_date, "finish_date": era.finish_date, "era": era}
        )
        new_stripes.append(
            {"start_date": start_date, "finish_date": finish_date, "era": era}
        )

        for old_stripe in old_stripes:
            for new_stripe in new_stripes:
                if (
                    not hh_after(old_stripe["start_date"], new_stripe["finish_date"])
                    and not hh_before(
                        old_stripe["finish_date"], new_stripe["start_date"]
                    )
                    and old_stripe["era"] != new_stripe["era"]
                ):
                    stripe_start = max(
                        old_stripe["start_date"], new_stripe["start_date"]
                    )
                    stripe_finish = (
                        old_stripe["finish_date"]
                        if hh_before(
                            old_stripe["finish_date"], new_stripe["finish_date"]
                        )
                        else new_stripe["finish_date"]
                    )
                    Supply._settle_stripe(
                        sess,
                        stripe_start,
                        stripe_finish,
                        old_stripe["era"],
                        new_stripe["era"],
                    )

        era.update(
            sess,
            start_date,
            finish_date,
            mop_contract,
            mop_account,
            dc_contract,
            dc_account,
            msn,
            pc,
            mtc_code,
            cop,
            comm,
            ssc_code,
            energisation_status,
            properties,
            imp_mpan_core,
            imp_llfc_code,
            imp_supplier_contract,
            imp_supplier_account,
            imp_sc,
            exp_mpan_core,
            exp_llfc_code,
            exp_supplier_contract,
            exp_supplier_account,
            exp_sc,
        )

        if prev_era is not None:
            prev_era.update_dates(sess, prev_era.start_date, prev_hh(start_date))

        if next_era is not None:
            next_era.update_dates(sess, next_hh(finish_date), next_era.finish_date)
        sess.flush()

    def insert_era_at(self, sess, start_date):
        if len(self.eras) == 0:
            raise BadRequest("Can't insert era as there aren't any existing eras")

        if hh_after(start_date, self.find_last_era(sess).finish_date):
            raise BadRequest(
                "One can't add an era that starts after the supply has finished."
            )

        first_era = self.find_first_era(sess)

        if start_date < first_era.start_date:
            template_era = first_era
        else:
            template_era = self.find_era_at(sess, start_date)

        logical_sites = []
        physical_site = None
        for site_era in template_era.site_eras:
            if site_era.is_physical:
                physical_site = site_era.site
            else:
                logical_sites.append(site_era.site)

        channel_set = set(
            [
                (imp_related, channel_type)
                for imp_related in [True, False]
                for channel_type in CHANNEL_TYPES
                if template_era.find_channel(sess, imp_related, channel_type)
                is not None
            ]
        )

        if template_era.imp_mpan_core is None:
            imp_llfc_code = None
        else:
            imp_llfc_code = template_era.imp_llfc.code

        if template_era.exp_mpan_core is None:
            exp_llfc_code = None
        else:
            exp_llfc_code = template_era.exp_llfc.code

        return self.insert_era(
            sess,
            physical_site,
            logical_sites,
            start_date,
            None,
            template_era.mop_contract,
            template_era.mop_account,
            template_era.dc_contract,
            template_era.dc_account,
            template_era.msn,
            template_era.pc,
            template_era.mtc_participant.mtc.code,
            template_era.cop,
            template_era.comm,
            None if template_era.ssc is None else template_era.ssc.code,
            template_era.energisation_status,
            template_era.dtc_meter_type,
            template_era.imp_mpan_core,
            imp_llfc_code,
            template_era.imp_supplier_contract,
            template_era.imp_supplier_account,
            template_era.imp_sc,
            template_era.exp_mpan_core,
            exp_llfc_code,
            template_era.exp_supplier_contract,
            template_era.exp_supplier_account,
            template_era.exp_sc,
            channel_set,
        )

    def insert_era(
        self,
        sess,
        physical_site,
        logical_sites,
        start_date,
        finish_date,
        mop_contract,
        mop_account,
        dc_contract,
        dc_account,
        msn,
        pc,
        mtc,
        cop,
        comm,
        ssc_code,
        energisation_status,
        properties,
        imp_mpan_core,
        imp_llfc_code,
        imp_supplier_contract,
        imp_supplier_account,
        imp_sc,
        exp_mpan_core,
        exp_llfc_code,
        exp_supplier_contract,
        exp_supplier_account,
        exp_sc,
        channel_set,
    ):
        covered_era = None

        if len(self.eras) > 0:
            if hh_after(start_date, self.find_last_era(sess).finish_date):
                raise BadRequest(
                    "One can't add a era that starts after the supply has finished."
                )

            first_era = self.find_first_era(sess)

            if hh_before(start_date, first_era.start_date):
                finish_date = prev_hh(first_era.start_date)
            else:
                covered_era = self.find_era_at(sess, start_date)
                if start_date == covered_era.start_date:
                    raise BadRequest("There's already an era with that start date.")

                finish_date = covered_era.finish_date

        for mc in (imp_mpan_core, exp_mpan_core):
            if mc is not None:
                sup = (
                    sess.query(Era)
                    .filter(
                        Era.supply != self,
                        or_(Era.imp_mpan_core == mc, Era.exp_mpan_core == mc),
                    )
                    .first()
                )
                if sup is not None:
                    raise BadRequest(
                        f"The MPAN core {mc} is already attached to another supply."
                    )

        sess.flush()
        with sess.no_autoflush:
            era = Era(
                sess,
                self,
                start_date,
                finish_date,
                mop_contract,
                mop_account,
                dc_contract,
                dc_account,
                msn,
                pc,
                mtc,
                cop,
                comm,
                ssc_code,
                energisation_status,
                properties,
                imp_mpan_core,
                imp_llfc_code,
                imp_supplier_contract,
                imp_supplier_account,
                imp_sc,
                exp_mpan_core,
                exp_llfc_code,
                exp_supplier_contract,
                exp_supplier_account,
                exp_sc,
            )
        sess.add(era)
        sess.flush()

        for imp_related, channel_type in sorted(list(channel_set)):
            sess.add(Channel(era, imp_related, channel_type))

        sess.flush()
        era.attach_site(sess, physical_site, True)
        for site in logical_sites:
            era.attach_site(sess, site, False)

        sess.flush()
        Supply._settle_stripe(sess, start_date, finish_date, covered_era, era)

        sess.flush()
        if covered_era is not None:
            covered_era.update_dates(sess, covered_era.start_date, start_date - HH)

        return era

    def find_first_era(self, sess):
        return (
            sess.query(Era).filter(Era.supply == self).order_by(Era.start_date).first()
        )

    def delete_era(self, sess, era):
        if len(self.eras) == 1:
            raise BadRequest(
                "The only way to delete the last era is to delete the entire supply."
            )

        prev_era = self.find_era_at(sess, prev_hh(era.start_date))
        if era.finish_date is None:
            next_era = None
        else:
            next_era = self.find_era_at(sess, next_hh(era.finish_date))

        Supply._settle_stripe(
            sess,
            era.start_date,
            era.finish_date,
            era,
            next_era if prev_era is None else prev_era,
        )

        if prev_era is None:
            next_era.update_dates(sess, era.start_date, next_era.finish_date)
        else:
            prev_era.update_dates(sess, prev_era.start_date, era.finish_date)

        for site_era in era.site_eras:
            sess.delete(site_era)
        sess.flush()
        for channel in era.channels:
            era.delete_channel(sess, channel.imp_related, channel.channel_type)
        sess.delete(era)
        sess.flush()

    def delete(self, sess):
        if len(self.bills) > 0:
            BadRequest(
                "One can't delete a supply if there are still bills attached to it."
            )

        for era in self.eras:
            for site_era in era.site_eras:
                sess.delete(site_era)
            sess.flush()
            for channel in era.channels:
                era.delete_channel(sess, channel.imp_related, channel.channel_type)
                sess.flush()
            sess.delete(era)
            sess.flush()

        sess.flush()

        sess.delete(self)
        sess.flush()

    def site_check(self, sess, start, finish):
        for era in self.eras:
            for imp_related in (True, False):
                era.find_channel(sess, imp_related, "ACTIVE").site_check(
                    sess, start, finish
                )


class Report(Base, PersistentClass):
    __tablename__ = "report"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    script = Column(Text, nullable=False)
    template = Column(Text, nullable=False)

    def __init__(self, name, script, template):
        self.name = name
        self.script = script
        self.template = template

    def update(self, name, script, template):
        self.name = name
        self.script = script
        self.template = template

    @classmethod
    def insert(cls, sess, name, script, template):
        report = cls(name, script, template)
        sess.add(report)
        sess.flush()
        return report


class SiteGroup:
    EXPORT_NET_GT_IMPORT_GEN = "Export to net > import from generators."
    EXPORT_GEN_GT_IMPORT = "Export to generators > import."
    EXPORT_3P_GT_IMPORT = "Export to 3rd party > import."

    def __init__(self, start_date, finish_date, sites, supplies):
        self.start_date = start_date
        self.finish_date = finish_date
        self.sites = sites
        self.supplies = supplies

    def hh_data(self, sess):
        caches = {}
        keys = {
            "net": {True: ["imp_net"], False: ["exp_net"]},
            "gen-net": {True: ["imp_net", "exp_gen"], False: ["exp_net", "imp_gen"]},
            "gen": {True: ["imp_gen"], False: ["exp_gen"]},
            "3rd-party": {True: ["imp_3p"], False: ["exp_3p"]},
            "3rd-party-reverse": {True: ["exp_3p"], False: ["imp_3p"]},
        }

        data = {
            hh_start: {
                "start_date": hh_start,
                "status": "A",
                "imp_net": 0,
                "exp_net": 0,
                "imp_gen": 0,
                "exp_gen": 0,
                "imp_3p": 0,
                "exp_3p": 0,
            }
            for hh_start in hh_range(caches, self.start_date, self.finish_date)
        }

        for channel in sess.scalars(
            select(Channel)
            .join(Era)
            .join(Supply)
            .join(Source)
            .where(
                Era.supply_id.in_([sup.id for sup in self.supplies]),
                Era.start_date <= self.finish_date,
                or_(Era.finish_date == null(), Era.finish_date >= self.start_date),
                Source.code != "sub",
                Channel.channel_type == "ACTIVE",
            )
        ):
            channel_keys = keys[channel.era.supply.source.code][channel.imp_related]

            chunk_start = hh_max(self.start_date, channel.era.start_date)
            chunk_finish = hh_min(self.finish_date, channel.era.finish_date)

            db_data = iter(
                sess.execute(
                    text(
                        "select start_date, value, channel_id, status from hh_datum "
                        "where channel_id = :channel_id "
                        "and start_date >= :start_date "
                        "and start_date <= :finish_date order by start_date"
                    ),
                    {
                        "channel_id": channel.id,
                        "start_date": chunk_start,
                        "finish_date": chunk_finish,
                    },
                )
            )

            hh = next(db_data, None)

            for hh_start in hh_range(caches, chunk_start, chunk_finish):
                dd = data[hh_start]
                if hh is not None and hh.start_date == hh_start:
                    if dd["status"] == "A" and hh.status != "A":
                        dd["status"] = "E"
                    for key in channel_keys:
                        dd[key] += hh.value
                    hh = next(db_data, None)
                else:
                    if dd["status"] == "A":
                        dd["status"] = "E"

                dd["displaced"] = dd["imp_gen"] - dd["exp_gen"] - dd["exp_net"]
                dd["used"] = (
                    dd["displaced"] + dd["imp_net"] + dd["imp_3p"] - dd["exp_3p"]
                )

        return data.values()

    def add_snag(self, sess, description, start_date, finish_date):
        return Snag.add_snag(
            sess, self.sites[0], None, description, start_date, finish_date
        )

    def delete_snag(self, sess, description, start_date, finish_date):
        Snag.remove_snag(
            sess, self.sites[0], None, description, start_date, finish_date
        )

    def hh_check(self, sess):
        resolve_1_start = resolve_1_finish = None
        snag_1_start = snag_1_finish = None
        resolve_2_start = resolve_2_finish = None
        snag_2_start = snag_2_finish = None
        resolve_3_start = resolve_3_finish = None
        snag_3_start = snag_3_finish = None

        for hh in self.hh_data(sess):
            hh_start_date = hh["start_date"]

            if hh["exp_net"] > hh["imp_gen"] and hh["status"] == "A":
                if snag_1_start is None:
                    snag_1_start = hh_start_date

                snag_1_finish = hh_start_date

                if resolve_1_start is not None:
                    self.delete_snag(
                        sess,
                        SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
                        resolve_1_start,
                        resolve_1_finish,
                    )
                    resolve_1_start = None
            else:
                if resolve_1_start is None:
                    resolve_1_start = hh_start_date

                resolve_1_finish = hh_start_date

                if snag_1_start is not None:
                    self.add_snag(
                        sess,
                        SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
                        snag_1_start,
                        snag_1_finish,
                    )
                    snag_1_start = None

            if hh["exp_gen"] > hh["imp_net"] + hh["imp_gen"] and hh["status"] == "A":
                if snag_2_start is None:
                    snag_2_start = hh_start_date

                snag_2_finish = hh_start_date

                if resolve_2_start is not None:
                    self.delete_snag(
                        sess,
                        SiteGroup.EXPORT_GEN_GT_IMPORT,
                        resolve_2_start,
                        resolve_2_finish,
                    )
                    resolve_2_start = None
            else:
                if resolve_2_start is None:
                    resolve_2_start = hh_start_date

                resolve_2_finish = hh_start_date

                if snag_2_start is not None:
                    self.add_snag(
                        sess,
                        SiteGroup.EXPORT_GEN_GT_IMPORT,
                        snag_2_start,
                        snag_2_finish,
                    )
                    snag_2_start = None

            if (
                hh["exp_3p"] > hh["imp_net"] + hh["imp_gen"] + hh["imp_3p"]
                and hh["status"] == "A"
            ):
                if snag_3_start is None:
                    snag_3_start = hh_start_date

                snag_3_finish = hh_start_date

                if resolve_3_start is not None:
                    self.delete_snag(
                        sess,
                        SiteGroup.EXPORT_3P_GT_IMPORT,
                        resolve_3_start,
                        resolve_3_finish,
                    )
                    resolve_3_start = None
            else:
                if resolve_3_start is None:
                    resolve_3_start = hh_start_date

                resolve_3_finish = hh_start_date

                if snag_3_start is not None:
                    self.add_snag(
                        sess,
                        SiteGroup.EXPORT_3P_GT_IMPORT,
                        snag_3_start,
                        snag_3_finish,
                    )
                    snag_3_start = None

        if snag_1_start is not None:
            self.add_snag(
                sess, SiteGroup.EXPORT_NET_GT_IMPORT_GEN, snag_1_start, snag_1_finish
            )

        if resolve_1_start is not None:
            self.delete_snag(
                sess,
                SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
                resolve_1_start,
                resolve_1_finish,
            )

        if snag_2_start is not None:
            self.add_snag(
                sess, SiteGroup.EXPORT_GEN_GT_IMPORT, snag_2_start, snag_2_finish
            )

        if resolve_2_start is not None:
            self.delete_snag(
                sess, SiteGroup.EXPORT_GEN_GT_IMPORT, resolve_2_start, resolve_2_finish
            )

        if snag_3_start is not None:
            self.add_snag(
                sess, SiteGroup.EXPORT_3P_GT_IMPORT, snag_3_start, snag_3_finish
            )

        if resolve_3_start is not None:
            self.delete_snag(
                sess, SiteGroup.EXPORT_3P_GT_IMPORT, resolve_3_start, resolve_3_finish
            )


class Scenario(Base, PersistentClass):
    @staticmethod
    def find_by_name(sess, name):
        return sess.query(Scenario).filter(Scenario.name == name).first()

    @staticmethod
    def get_by_name(sess, name):
        scenario = Scenario.find_by_name(sess, name)
        if scenario is None:
            raise NotFound(f"There isn't a scenario with the name '{name}'.")
        return scenario

    @staticmethod
    def insert(sess, name, properties):
        scenario = Scenario(name, properties)
        sess.add(scenario)
        sess.flush()
        return scenario

    __tablename__ = "scenario"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    properties = Column(Text, nullable=False)

    def __init__(self, name, properties):
        self.update(name, properties)

    def update(self, name, properties):
        name = name.strip()
        if len(name) == 0:
            raise BadRequest("The scenario name can't be blank.")
        self.name = name
        self.properties = dumps(properties)
        for required in (
            "scenario_start_year",
            "scenario_start_month",
        ):
            if required not in properties:
                raise BadRequest(
                    f"The field '{required}' is required in the scenario properties"
                )

        for name in ("local_rates", "industry_rates"):
            lst = properties.get(name, [])
            if not isinstance(lst, list):
                raise BadRequest(f"The '{name}' must be a list.")
            for v in lst:
                if not isinstance(v, dict):
                    raise BadRequest(f"The values in {name} must be maps.")

    def delete(self, sess):
        sess.delete(self)

    @property
    def props(self):
        if not hasattr(self, "_props"):
            self._props = loads(self.properties)
        return self._props


class GRegisterRead(Base, PersistentClass):
    __tablename__ = "g_register_read"
    id = Column("id", Integer, primary_key=True)
    g_bill_id = Column(
        Integer, ForeignKey("g_bill.id", ondelete="CASCADE"), nullable=False, index=True
    )
    msn = Column(String, nullable=False, index=True)
    g_unit_id = Column(Integer, ForeignKey("g_unit.id"), nullable=False, index=True)
    g_unit = relationship("GUnit", primaryjoin="GUnit.id==GRegisterRead.g_unit_id")
    correction_factor = Column(Numeric)
    calorific_value = Column(Numeric)
    prev_date = Column(DateTime(timezone=True), nullable=False, index=True)
    prev_value = Column(Numeric, nullable=False)
    prev_type_id = Column(Integer, ForeignKey("g_read_type.id"), index=True)
    prev_type = relationship(
        "GReadType", primaryjoin="GReadType.id==GRegisterRead.prev_type_id"
    )
    pres_date = Column(DateTime(timezone=True), nullable=False, index=True)
    pres_value = Column(Numeric, nullable=False)
    pres_type_id = Column(Integer, ForeignKey("g_read_type.id"), index=True)
    pres_type = relationship(
        "GReadType", primaryjoin="GReadType.id==GRegisterRead.pres_type_id"
    )

    def __init__(
        self,
        g_bill,
        msn,
        g_unit,
        correction_factor,
        calorific_value,
        prev_value,
        prev_date,
        prev_type,
        pres_value,
        pres_date,
        pres_type,
    ):
        self.g_bill = g_bill
        self.update(
            msn,
            g_unit,
            correction_factor,
            calorific_value,
            prev_value,
            prev_date,
            prev_type,
            pres_value,
            pres_date,
            pres_type,
        )

    def update(
        self,
        msn,
        g_unit,
        correction_factor,
        calorific_value,
        prev_value,
        prev_date,
        prev_type,
        pres_value,
        pres_date,
        pres_type,
    ):
        self.msn = msn
        self.g_unit = g_unit
        self.correction_factor = correction_factor
        self.calorific_value = calorific_value
        self.prev_value = prev_value
        self.prev_date = prev_date
        self.prev_type = prev_type
        self.pres_value = pres_value
        self.pres_date = pres_date
        self.pres_type = pres_type

    def delete(self, sess):
        sess.delete(self)
        sess.flush()


class SiteGEra(Base, PersistentClass):
    __tablename__ = "site_g_era"
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("site.id"))
    g_era_id = Column(Integer, ForeignKey("g_era.id"))
    is_physical = Column(Boolean, nullable=False)

    def __init__(self, site, g_era, is_physical):
        self.site = site
        self.g_era = g_era
        self.is_physical = is_physical


class GEra(Base, PersistentClass):
    __tablename__ = "g_era"
    id = Column("id", Integer, primary_key=True)
    g_supply_id = Column(Integer, ForeignKey("g_supply.id"), nullable=False, index=True)
    site_g_eras = relationship("SiteGEra", backref="g_era")
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    finish_date = Column(DateTime(timezone=True), index=True)
    msn = Column(String)
    correction_factor = Column(Numeric, nullable=False)
    aq = Column(Numeric, nullable=False)
    soq = Column(Numeric, nullable=False)

    g_unit_id = Column(Integer, ForeignKey("g_unit.id"), nullable=False, index=True)
    g_unit = relationship("GUnit", primaryjoin="GUnit.id==GEra.g_unit_id")
    g_contract_id = Column(
        Integer, ForeignKey("g_contract.id"), nullable=False, index=True
    )
    g_contract = relationship(
        "GContract", primaryjoin="GContract.id==GEra.g_contract_id"
    )
    account = Column(String, nullable=False)
    g_reading_frequency_id = Column(
        Integer, ForeignKey("g_reading_frequency.id"), nullable=False, index=True
    )
    g_reading_frequency = relationship(
        "GReadingFrequency",
        primaryjoin="GReadingFrequency.id==GEra.g_reading_frequency_id",
    )

    def __init__(
        self,
        sess,
        g_supply,
        start_date,
        finish_date,
        msn,
        correction_factor,
        g_unit,
        contract,
        account,
        g_reading_frequency,
        aq,
        soq,
    ):
        self.g_supply = g_supply
        self.update(
            sess,
            start_date,
            finish_date,
            msn,
            correction_factor,
            g_unit,
            contract,
            account,
            g_reading_frequency,
            aq,
            soq,
        )

    def attach_site(self, sess, site, is_location=False):
        if (
            sess.query(SiteGEra)
            .filter(SiteGEra.g_era == self, SiteGEra.site == site)
            .count()
            == 1
        ):
            raise BadRequest("The site is already attached to this supply.")

        site_g_era = SiteGEra(site, self, False)
        sess.add(site_g_era)
        sess.flush()
        if is_location:
            self.set_physical_location(sess, site)

    def detach_site(self, sess, site):
        site_g_era = (
            sess.query(SiteGEra)
            .filter(SiteGEra.g_era == self, SiteGEra.site == site)
            .first()
        )
        if site_g_era is None:
            raise BadRequest(
                "Can't detach this era from this site, as it isn't attached."
            )
        if site_g_era.is_physical:
            raise BadRequest(
                "You can't detach an era from the site where it is physically located."
            )

        sess.delete(site_g_era)
        sess.flush()

    def update_dates(self, sess, start_date, finish_date):
        if start_date == self.start_date and finish_date == self.finish_date:
            return
        else:
            self.update(
                sess,
                start_date,
                finish_date,
                self.msn,
                self.correction_factor,
                self.g_unit,
                self.g_contract,
                self.account,
                self.g_reading_frequency,
                self.aq,
                self.soq,
            )

    def update(
        self,
        sess,
        start_date,
        finish_date,
        msn,
        correction_factor,
        g_unit,
        g_contract,
        account,
        g_reading_frequency,
        aq,
        soq,
    ):
        if hh_after(start_date, finish_date):
            raise BadRequest("The era start date can't be after the finish date.")

        self.start_date = start_date
        self.finish_date = finish_date
        self.msn = msn
        self.correction_factor = correction_factor
        self.g_unit = g_unit
        self.g_contract = g_contract
        self.account = account
        self.g_reading_frequency = g_reading_frequency
        self.aq = aq
        self.soq = soq

        with sess.no_autoflush:
            if g_contract.start_g_rate_script.start_date > start_date:
                raise BadRequest("The contract starts after the era.")

        if hh_before(g_contract.finish_g_rate_script.finish_date, finish_date):
            raise BadRequest("The contract finishes before the era.")

    def set_physical_location(self, sess, site):
        target_ssgen = (
            sess.query(SiteGEra)
            .filter(SiteGEra.g_era == self, SiteGEra.site == site)
            .first()
        )
        if target_ssgen is None:
            raise BadRequest("The site isn't attached to this supply.")

        for ssgen in self.site_g_eras:
            ssgen.is_physical = ssgen == target_ssgen
        sess.flush()


class GSupply(Base, PersistentClass):
    __tablename__ = "g_supply"
    id = Column("id", Integer, primary_key=True)
    mprn = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    g_exit_zone_id = Column(
        Integer, ForeignKey("g_exit_zone.id"), nullable=False, index=True
    )
    g_exit_zone = relationship(
        "GExitZone", primaryjoin="GExitZone.id==GSupply.g_exit_zone_id"
    )
    note = Column(Text, nullable=False)
    g_eras = relationship("GEra", backref="g_supply")
    g_bills = relationship("GBill", backref="g_supply")

    def __init__(self, mprn, name, g_exit_zone, note):
        self.update(mprn, name, g_exit_zone)
        self.note = note

    def update(self, mprn, name, g_exit_zone):
        self.g_exit_zone = g_exit_zone
        name = name.strip()
        if len(name) == 0:
            raise BadRequest("The supply name can't be blank.")

        self.name = name
        mprn = mprn.strip()
        if len(mprn) == 0:
            raise BadRequest("The MPRN can't be blank.")
        self.mprn = mprn

    @staticmethod
    def find_by_mprn(sess, mprn):
        return sess.query(GSupply).filter(GSupply.mprn == mprn).first()

    @staticmethod
    def get_by_mprn(sess, mprn):
        supply = GSupply.find_by_mprn(sess, mprn)
        if supply is None:
            raise BadRequest(f"The MPRN {mprn} is not set up in Chellow.")
        return supply

    def insert_g_era_at(self, sess, start_date):
        g_era = self.find_g_era_at(sess, start_date)
        physical_site = (
            sess.query(Site)
            .join(SiteGEra)
            .filter(SiteGEra.is_physical == true(), SiteGEra.g_era == g_era)
            .one()
        )
        logical_sites = (
            sess.query(Site)
            .join(SiteGEra)
            .filter(SiteGEra.is_physical == false(), SiteGEra.g_era == g_era)
            .all()
        )
        return self.insert_g_era(
            sess,
            physical_site,
            logical_sites,
            start_date,
            g_era.finish_date,
            g_era.msn,
            g_era.correction_factor,
            g_era.g_unit,
            g_era.g_contract,
            g_era.account,
            g_era.g_reading_frequency,
            g_era.aq,
            g_era.soq,
        )

    def insert_g_era(
        self,
        sess,
        physical_site,
        logical_sites,
        start_date,
        finish_date,
        msn,
        correction_factor,
        g_unit,
        g_contract,
        account,
        g_reading_frequency,
        aq,
        soq,
    ):
        covered_g_era = None
        last_g_era = (
            sess.query(GEra)
            .filter(GEra.g_supply == self)
            .order_by(GEra.start_date.desc())
            .first()
        )
        if last_g_era is not None:
            if hh_after(start_date, last_g_era.finish_date):
                raise BadRequest(
                    "One can't add a era that starts after " "the supply has finished."
                )

            first_g_era = (
                sess.query(GEra)
                .filter(GEra.g_supply == self)
                .order_by(GEra.start_date)
                .first()
            )

            if hh_before(start_date, first_g_era.start_date):
                finish_date = prev_hh(first_g_era.start_date)
            else:
                covered_g_era = self.find_g_era_at(sess, start_date)
                if start_date == covered_g_era.start_date:
                    raise BadRequest("There's already an era with that start date.")

                finish_date = covered_g_era.finish_date

        g_era = GEra(
            sess,
            self,
            start_date,
            finish_date,
            msn,
            correction_factor,
            g_unit,
            g_contract,
            account,
            g_reading_frequency,
            aq,
            soq,
        )
        sess.add(g_era)

        g_era.attach_site(sess, physical_site, True)
        for site in logical_sites:
            g_era.attach_site(sess, site, False)

        if covered_g_era is not None:
            covered_g_era.update_dates(sess, covered_g_era.start_date, start_date - HH)
        return g_era

    def attach_site(self, sess, site, is_location=False):
        if site in sess.query(Site).join(SiteGEra).filter(SiteGEra.g_era == self).all():
            raise BadRequest("The site is already attached to this supply.")

        site_era = SiteGEra(site, self, False)
        sess.add(site_era)
        sess.flush()
        if is_location:
            self.set_physical_location(sess, site)

    def detach_site(self, sess, site):
        site_era = (
            sess.query(SiteGEra)
            .filter(SiteGEra.era == self, SiteEra.site == site)
            .first()
        )
        if site_era is None:
            raise BadRequest(
                "Can't detach this era from this site, as it isn't attached."
            )
        if site_era.is_physical:
            raise BadRequest(
                "You can't detach an era from the site where it is "
                "physically located."
            )

        sess.delete(site_era)
        sess.flush()

    def update_g_era(
        self,
        sess,
        g_era,
        start_date,
        finish_date,
        msn,
        correction_factor,
        g_unit,
        g_contract,
        account,
        g_reading_frequency,
        aq,
        soq,
    ):
        if g_era.g_supply != self:
            raise Exception("The era doesn't belong to this supply.")

        prev_g_era = self.find_g_era_at(sess, prev_hh(g_era.start_date))
        if g_era.finish_date is None:
            next_g_era = None
        else:
            next_g_era = self.find_g_era_at(sess, next_hh(g_era.finish_date))

        g_era.update(
            sess,
            start_date,
            finish_date,
            msn,
            correction_factor,
            g_unit,
            g_contract,
            account,
            g_reading_frequency,
            aq,
            soq,
        )

        if prev_g_era is not None:
            prev_g_era.update_dates(sess, prev_g_era.start_date, prev_hh(start_date))

        if next_g_era is not None:
            next_g_era.update_dates(sess, next_hh(finish_date), next_g_era.finish_date)

    def find_g_era_at(self, sess, dt):
        if dt is None:
            return (
                sess.query(GEra)
                .filter(GEra.g_supply == self, GEra.finish_date == null())
                .first()
            )
        else:
            return (
                sess.query(GEra)
                .filter(
                    GEra.g_supply == self,
                    GEra.start_date <= dt,
                    or_(GEra.finish_date == null(), GEra.finish_date >= dt),
                )
                .first()
            )

    def find_g_eras(self, sess, start, finish):
        g_eras = (
            sess.query(GEra)
            .filter(
                GEra.g_supply == self,
                or_(GEra.finish_date == null(), GEra.finish_date >= start),
            )
            .order_by(GEra.start_date)
        )
        if finish is not None:
            g_eras = g_eras.filter(GEra.start_date <= finish)
        return g_eras.all()

    def delete(self, sess):
        if len(self.g_bills) > 0:
            raise BadRequest(
                "One can't delete a supply if there are still " "bills attached to it."
            )

        for g_era in self.g_eras:
            for site_g_era in g_era.site_g_eras:
                sess.delete(site_g_era)
            sess.flush()
            sess.delete(g_era)
            sess.flush()

        sess.delete(self)
        sess.flush()

    def delete_g_era(self, sess, g_era):
        if len(self.g_eras) == 1:
            raise BadRequest(
                "The only way to delete the last era is to " "delete the entire supply."
            )

        prev_g_era = self.find_g_era_at(sess, prev_hh(g_era.start_date))
        if g_era.finish_date is None:
            next_g_era = None
        else:
            next_g_era = self.find_g_era_at(sess, next_hh(g_era.finish_date))

        if prev_g_era is None:
            next_g_era.update_dates(sess, g_era.start_date, next_g_era.finish_date)
        else:
            prev_g_era.update_dates(sess, prev_g_era.start_date, g_era.finish_date)

        for site_g_era in g_era.site_g_eras:
            sess.delete(site_g_era)
        sess.flush()
        sess.delete(g_era)
        sess.flush()


class GBill(Base, PersistentClass):
    __tablename__ = "g_bill"
    id = Column("id", Integer, primary_key=True)
    g_batch_id = Column(Integer, ForeignKey("g_batch.id"), nullable=False, index=True)
    g_supply_id = Column(Integer, ForeignKey("g_supply.id"), nullable=False, index=True)
    bill_type_id = Column(Integer, ForeignKey("bill_type.id"), index=True)
    bill_type = relationship("BillType", primaryjoin="BillType.id==GBill.bill_type_id")
    reference = Column(String, nullable=False)
    account = Column(String, nullable=False)
    issue_date = Column(DateTime(timezone=True), nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    finish_date = Column(DateTime(timezone=True), nullable=False, index=True)
    kwh = Column(Numeric, nullable=False)
    net = Column(Numeric, nullable=False)
    vat = Column(Numeric, nullable=False)
    gross = Column(Numeric, nullable=False)
    raw_lines = Column(Text, nullable=False)
    breakdown = Column(Text, nullable=False)
    g_reads = relationship(
        "GRegisterRead",
        backref="g_bill",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(
        self,
        g_batch,
        g_supply,
        bill_type,
        reference,
        account,
        issue_date,
        start_date,
        finish_date,
        kwh,
        net,
        vat,
        gross,
        raw_lines,
        breakdown,
    ):
        self.g_batch = g_batch
        self.g_supply = g_supply
        self.update(
            bill_type,
            reference,
            account,
            issue_date,
            start_date,
            finish_date,
            kwh,
            net,
            vat,
            gross,
            raw_lines,
            breakdown,
        )

    def update(
        self,
        bill_type,
        reference,
        account,
        issue_date,
        start_date,
        finish_date,
        kwh,
        net,
        vat,
        gross,
        raw_lines,
        breakdown,
    ):
        self.bill_type = bill_type
        self.reference = reference
        self.account = account
        self.issue_date = issue_date
        self.start_date = start_date
        self.finish_date = finish_date
        for name, val in (("net", net), ("vat", vat), ("gross", gross)):
            if val.as_tuple().exponent != -2:
                raise BadRequest(
                    "The bill field '" + name + "' must have exactly two "
                    "decimal places. It's actually: " + str(val) + "."
                )
        self.kwh = kwh
        self.net = net
        self.vat = vat
        self.gross = gross
        self.raw_lines = raw_lines
        self.breakdown = dumps(breakdown)

    def insert_g_read(
        self,
        sess,
        msn,
        g_units,
        correction_factor,
        calorific_value,
        prev_value,
        prev_date,
        prev_type,
        pres_value,
        pres_date,
        pres_type,
    ):
        read = GRegisterRead(
            self,
            msn,
            g_units,
            correction_factor,
            calorific_value,
            prev_value,
            prev_date,
            prev_type,
            pres_value,
            pres_date,
            pres_type,
        )
        sess.add(read)
        sess.flush()
        return read

    def delete(self, sess):
        sess.delete(self)
        sess.flush()

    def make_breakdown(self):
        return loads(self.breakdown)


class GBatch(Base, PersistentClass):
    __tablename__ = "g_batch"
    id = Column("id", Integer, primary_key=True)
    g_contract_id = Column(
        Integer, ForeignKey("g_contract.id"), nullable=False, index=True
    )
    reference = Column(String, nullable=False)
    description = Column(String, nullable=False)
    bills = relationship("GBill", backref="g_batch")
    __table_args__ = (UniqueConstraint("g_contract_id", "reference"),)

    def __init__(self, sess, g_contract, reference, description):
        self.g_contract = g_contract
        self._update(sess, reference, description)

    def _update(self, sess, reference, description):
        reference = reference.strip()
        if len(reference) == 0:
            raise BadRequest("The batch reference can't be blank.")

        self.reference = reference
        self.description = description.strip()

    def update(self, sess, reference, description):
        self._update(sess, reference, description)
        try:
            sess.flush()
        except SQLAlchemyError:
            sess.rollback()
            raise BadRequest(
                f"There's already a batch attached to the contract "
                f"{self.g_contract.name} with the reference {reference}."
            )

    def delete(self, sess):
        sess.execute(delete(GBill).where(GBill.g_batch == self))
        sess.delete(self)
        sess.flush()

    def insert_g_bill(
        self,
        sess,
        g_supply,
        bill_type,
        reference,
        account,
        issue_date,
        start_date,
        finish_date,
        kwh,
        net_gbp,
        vat_gbp,
        gross_gbp,
        raw_lines,
        breakdown,
    ):
        g_bill = GBill(
            self,
            g_supply,
            bill_type,
            reference,
            account,
            issue_date,
            start_date,
            finish_date,
            kwh,
            net_gbp,
            vat_gbp,
            gross_gbp,
            raw_lines,
            breakdown,
        )

        sess.add(g_bill)
        sess.flush()
        return g_bill


class GReadingFrequency(Base, PersistentClass):
    __tablename__ = "g_reading_frequency"
    id = Column("id", Integer, primary_key=True)
    code = Column(String, nullable=False)
    description = Column(String, nullable=False)

    def __init__(self, code, description):
        self.code = code
        self.description = description

    @staticmethod
    def insert(sess, code, description):
        g_reading_frequency = GReadingFrequency(code, description)
        sess.add(g_reading_frequency)
        return g_reading_frequency

    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        freq = sess.query(GReadingFrequency).filter_by(code=code).first()
        if freq is None:
            raise BadRequest(f"The Reading Frequency with code {code} can't be found.")
        return freq


class GContract(Base, PersistentClass):
    __tablename__ = "g_contract"
    id = Column("id", Integer, primary_key=True)
    is_industry = Column(Boolean, nullable=False, index=True)
    name = Column(String, nullable=False)
    charge_script = Column(Text, nullable=False)
    properties = Column(Text, nullable=False)
    state = Column(Text, nullable=False)
    g_rate_scripts = relationship(
        "GRateScript",
        back_populates="g_contract",
        primaryjoin="GContract.id==GRateScript.g_contract_id",
    )
    g_batches = relationship("GBatch", backref="g_contract")
    __table_args__ = (UniqueConstraint("is_industry", "name"),)

    start_g_rate_script_id = Column(
        Integer,
        ForeignKey(
            "g_rate_script.id",
            use_alter=True,
            name="g_contract_start_g_rate_script_id_fkey",
        ),
    )
    finish_g_rate_script_id = Column(
        Integer,
        ForeignKey(
            "g_rate_script.id",
            use_alter=True,
            name="g_contract_finish_g_rate_script_id_fkey",
        ),
    )

    start_g_rate_script = relationship(
        "GRateScript", primaryjoin="GRateScript.id==GContract.start_g_rate_script_id"
    )
    finish_g_rate_script = relationship(
        "GRateScript", primaryjoin="GRateScript.id==GContract.finish_g_rate_script_id"
    )

    def __init__(self, is_industry, name, charge_script, properties):
        self.is_industry = is_industry
        self.update(name, charge_script, properties)
        self.update_state({})

    def update(self, name, charge_script, properties):
        name = name.strip()
        if len(name) == 0:
            raise BadRequest("The gas contract name can't be blank.")
        self.name = name

        try:
            parse(charge_script)
        except SyntaxError as e:
            raise BadRequest(str(e))
        except NameError as e:
            raise BadRequest(str(e))
        self.charge_script = charge_script

        if not isinstance(properties, dict):
            raise BadRequest("The 'properties' argument must be a dictionary.")
        self.properties = dumps(properties)

    def update_state(self, state):
        if not isinstance(state, dict):
            raise BadRequest("The 'state' argument must be a dictionary.")
        self.state = dumps(state)

    def update_g_rate_script(self, sess, rscript, start_date, finish_date, script):
        if rscript.g_contract != self:
            raise Exception("This gas rate script doesn't belong to this contract.")

        if start_date is None:
            raise BadRequest("The start date can't be None.")

        if hh_after(start_date, finish_date):
            raise BadRequest("The start date can't be after the finish date.")

        if not isinstance(script, dict):
            raise Exception("The gas rate script must be a dictionary.")
        rscript.script = dumps(script)

        prev_rscript = self.find_g_rate_script_at(sess, rscript.start_date - HH)
        if rscript.finish_date is None:
            next_rscript = None
        else:
            next_rscript = self.find_g_rate_script_at(sess, rscript.finish_date + HH)

        rscript.start_date = start_date
        rscript.finish_date = finish_date

        if prev_rscript is not None:
            if not hh_before(prev_rscript.start_date, start_date):
                raise BadRequest(
                    "The start date must be after the start date of the "
                    "previous rate script."
                )
            prev_rscript.finish_date = prev_hh(start_date)

        if next_rscript is not None:
            if finish_date is None:
                raise BadRequest(
                    "The finish date must be before the finish date of the "
                    "next rate script."
                )

            if not hh_before(finish_date, next_rscript.finish_date):
                raise BadRequest(
                    "The finish date must be before the finish date of the "
                    "next rate script."
                )

            next_rscript.start_date = next_hh(finish_date)

        sess.flush()
        rscripts = (
            sess.query(GRateScript)
            .filter(GRateScript.g_contract == self)
            .order_by(GRateScript.start_date)
            .all()
        )
        self.start_g_rate_script = rscripts[0]
        self.finish_g_rate_script = rscripts[-1]

        eras_before = (
            sess.query(GEra)
            .filter(
                GEra.start_date < self.start_g_rate_script.start_date,
                GEra.g_contract == self,
            )
            .all()
        )
        if len(eras_before) > 0:
            raise BadRequest(
                f"The era with MPRN {eras_before[0].g_supply.mprn} exists before the "
                f"start of this contract, and is attached to this contract."
            )

        if self.finish_g_rate_script.finish_date is not None:
            eras_after = (
                sess.query(GEra)
                .filter(
                    GEra.finish_date > self.finish_g_rate_script.finish_date,
                    GEra.g_contract == self,
                )
                .all()
            )
            if len(eras_after) > 0:
                raise BadRequest(
                    f"The era with MPRN {eras_after[0].g_supply.mprn} exists after the "
                    f"start of this contract, and is attached to this contract."
                )

    def delete(self, sess):
        if len(self.g_batches) > 0:
            raise BadRequest(
                "You can't delete a contract that still has batches attached " "to it."
            )
        if sess.query(GEra).filter(GEra.g_contract == self).count() > 0:
            raise BadRequest(
                "You can't delete a contract that is still used in an era."
            )

        self.g_rate_scripts[:] = []
        sess.delete(self)

    def delete_g_rate_script(self, sess, rscript):
        if rscript.g_contract != self:
            raise Exception(
                "The rate script to delete isn't assocated with this " "contract."
            )
        rscripts = (
            sess.query(GRateScript)
            .filter(GRateScript.g_contract == self)
            .order_by(GRateScript.start_date)
            .all()
        )

        if len(rscripts) < 2:
            raise BadRequest("You can't delete the last rate script.")

        if rscripts[0] == rscript:
            self.start_g_rate_script = rscripts[1]
        elif rscripts[-1] == rscript:
            self.finish_g_rate_script = rscripts[-2]

        sess.flush()
        sess.delete(rscript)
        sess.flush()

        if rscripts[0] == rscript:
            rscripts[1].start_date = rscript.start_date
        elif rscripts[-1] == rscript:
            rscripts[-2].finish_date = rscript.finish_date
        else:
            prev_script = self.find_g_rate_script_at(sess, rscript.start_date - HH)
            prev_script.finish_date = rscript.finish_date

    def find_g_rate_script_at(self, sess, date):
        return (
            sess.query(GRateScript)
            .filter(
                GRateScript.g_contract == self,
                GRateScript.start_date <= date,
                or_(GRateScript.finish_date == null(), GRateScript.finish_date >= date),
            )
            .first()
        )

    def insert_g_rate_script(self, sess, start_date, script):
        scripts = (
            sess.query(GRateScript)
            .filter(GRateScript.g_contract == self)
            .order_by(GRateScript.start_date)
            .all()
        )
        if len(scripts) == 0:
            finish_date = None
        else:
            if hh_after(start_date, scripts[-1].finish_date):
                raise BadRequest(
                    f"For the gas contract {self.id} called {self.name}, the start "
                    f"date {start_date} is after the last rate script."
                )

            covered_script = self.find_g_rate_script_at(sess, start_date)
            if covered_script is None:
                finish_date = scripts[0].start_date - HH
            else:
                if covered_script.start_date == covered_script.finish_date:
                    raise BadRequest(
                        "The start date falls on a rate script which is only half an "
                        "hour in length, and so cannot be divided."
                    )
                if start_date == covered_script.start_date:
                    raise BadRequest(
                        "The start date is the same as the start date of an existing "
                        "rate script."
                    )

                finish_date = covered_script.finish_date
                covered_script.finish_date = prev_hh(start_date)
                sess.flush()

        new_script = GRateScript(self, start_date, finish_date, script)
        sess.add(new_script)
        sess.flush()
        rscripts = (
            sess.query(GRateScript)
            .filter(GRateScript.g_contract == self)
            .order_by(GRateScript.start_date)
            .all()
        )
        self.start_g_rate_script = rscripts[0]
        self.finish_g_rate_script = rscripts[-1]
        sess.flush()
        return new_script

    def insert_g_batch(self, sess, reference, description):
        batch = GBatch(sess, self, reference, description)
        try:
            sess.add(batch)
        except ProgrammingError:
            raise BadRequest("There's already a batch with that reference.")
        return batch

    def make_properties(self):
        return loads(self.properties)

    def make_state(self):
        return loads(self.state)

    def find_g_batch_by_reference(self, sess, reference):
        return (
            sess.query(GBatch)
            .filter(GBatch.g_contract == self, GBatch.reference == reference)
            .first()
        )

    def get_g_batch_by_reference(self, sess, reference):
        batch = self.find_g_batch_by_reference(sess, reference)
        if batch is None:
            raise BadRequest(f"Can't find the batch with reference {reference}")
        return batch

    @staticmethod
    def insert(
        sess,
        is_industry,
        name,
        charge_script,
        properties,
        start_date,
        finish_date,
        rate_script,
    ):
        contract = GContract(is_industry, name, charge_script, properties)
        sess.add(contract)
        sess.flush()
        rscript = contract.insert_g_rate_script(sess, start_date, rate_script)
        contract.update_g_rate_script(
            sess, rscript, start_date, finish_date, rate_script
        )
        return contract

    @classmethod
    def insert_industry(
        cls,
        sess,
        name,
        charge_script,
        properties,
        start_date,
        finish_date,
        rate_script,
    ):
        return cls.insert(
            sess,
            True,
            name,
            charge_script,
            properties,
            start_date,
            finish_date,
            rate_script,
        )

    @classmethod
    def insert_supplier(
        cls,
        sess,
        name,
        charge_script,
        properties,
        start_date,
        finish_date,
        rate_script,
    ):
        return cls.insert(
            sess,
            False,
            name,
            charge_script,
            properties,
            start_date,
            finish_date,
            rate_script,
        )

    @staticmethod
    def get_supplier_by_id(sess, oid):
        return sess.execute(
            select(GContract).where(
                GContract.id == oid, GContract.is_industry == false()
            )
        ).scalar_one()

    @staticmethod
    def get_industry_by_id(sess, oid):
        return sess.execute(
            select(GContract).where(
                GContract.id == oid, GContract.is_industry == true()
            )
        ).scalar_one()

    @classmethod
    def get_industry_by_name(cls, sess, name):
        cont = cls.find_industry_by_name(sess, name)
        if cont is None:
            raise BadRequest(
                f"There isn't a gas industry contract with the name '{name}'."
            )
        return cont

    @staticmethod
    def find_industry_by_name(sess, name):
        return sess.execute(
            select(GContract).where(
                GContract.is_industry == true(), GContract.name == name
            )
        ).scalar_one_or_none()

    @classmethod
    def get_supplier_by_name(cls, sess, name):
        cont = cls.find_supplier_by_name(sess, name)
        if cont is None:
            raise BadRequest(
                f"There isn't a gas supplier contract with the name '{name}'."
            )
        return cont

    @staticmethod
    def find_supplier_by_name(sess, name):
        return sess.execute(
            select(GContract).where(
                GContract.is_industry == false(), GContract.name == name
            )
        ).scalar_one_or_none()


class GRateScript(Base, PersistentClass):
    __tablename__ = "g_rate_script"
    id = Column("id", Integer, primary_key=True)
    g_contract_id = Column(Integer, ForeignKey("g_contract.id"), index=True)
    g_contract = relationship(
        "GContract",
        back_populates="g_rate_scripts",
        primaryjoin="GContract.id==GRateScript.g_contract_id",
    )
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    finish_date = Column(DateTime(timezone=True), nullable=True, index=True)
    script = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint("g_contract_id", "start_date"),)

    def __init__(self, g_contract, start_date, finish_date, script):
        self.g_contract = g_contract
        self.start_date = start_date
        self.finish_date = finish_date
        self.update(script)

    def update(self, script_dictionary):
        if not isinstance(script_dictionary, dict):
            raise Exception(
                f"The script_dictionary must be a dictionary, but found a "
                f"{type(script_dictionary)}"
            )
        self.script = dumps(script_dictionary)

    def make_script(self):
        return loads(self.script)


class GUnit(Base, PersistentClass):
    __tablename__ = "g_unit"
    id = Column("id", Integer, primary_key=True)
    code = Column(String, nullable=False, index=True, unique=True)
    description = Column(String, nullable=False)
    factor = Column(Numeric, nullable=False)

    def __init__(self, code, description, factor):
        self.code = code
        self.description = description
        self.factor = factor

    @staticmethod
    def insert(sess, code, description, factor):
        g_unit = GUnit(code, description, factor)
        sess.add(g_unit)
        return g_unit

    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        typ = sess.query(GUnit).filter_by(code=code).first()
        if typ is None:
            raise BadRequest(f"The gas unit with code {code} can't be found.")
        return typ


class GDn(Base, PersistentClass):
    __tablename__ = "g_dn"
    id = Column("id", Integer, primary_key=True)
    code = Column(String, nullable=False, index=True, unique=True)
    name = Column(String, nullable=False, index=True, unique=True)
    g_ldzs = relationship("GLdz", backref="g_dn")

    def __init__(self, code, name):
        self.code = code
        self.name = name

    def insert_g_ldz(self, sess, code):
        g_ldz = GLdz(self, code)
        sess.add(g_ldz)
        return g_ldz

    @staticmethod
    def insert(sess, code, name):
        g_dn = GDn(code, name)
        sess.add(g_dn)
        return g_dn

    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        dn = sess.query(GDn).filter_by(code=code).first()
        if dn is None:
            raise BadRequest(f"The GDN with code {code} can't be found.")
        return dn


class GLdz(Base, PersistentClass):
    __tablename__ = "g_ldz"
    id = Column("id", Integer, primary_key=True)
    g_dn_id = Column(Integer, ForeignKey("g_dn.id"), index=True, nullable=False)
    code = Column(String, nullable=False, index=True, unique=True)
    g_exit_zones = relationship("GExitZone", backref="g_ldz")

    def __init__(self, g_dn, code):
        self.g_dn = g_dn
        self.code = code

    def insert_g_exit_zone(self, sess, code):
        g_exit_zone = GExitZone(self, code)
        sess.add(g_exit_zone)
        return g_exit_zone

    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        typ = sess.query(GLdz).filter_by(code=code).first()
        if typ is None:
            raise BadRequest(f"The LDZ with code {code} can't be found.")
        return typ


class GExitZone(Base, PersistentClass):
    __tablename__ = "g_exit_zone"
    id = Column("id", Integer, primary_key=True)
    g_ldz_id = Column(Integer, ForeignKey("g_ldz.id"), index=True, nullable=False)
    code = Column(String, nullable=False, index=True, unique=True)

    def __init__(self, g_ldz, code):
        self.g_ldz = g_ldz
        self.code = code

    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        typ = sess.query(GExitZone).filter_by(code=code).first()
        if typ is None:
            raise BadRequest(f"The Exit Zone with code {code} can't be found.")
        return typ


class ReportRun(Base, PersistentClass):
    __tablename__ = "report_run"
    id = Column(Integer, primary_key=True)
    date_created = Column(DateTime(timezone=True), nullable=False, index=True)
    creator = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False, index=True)
    state = Column(String, nullable=False, index=True)
    data = Column(JSONB, nullable=False)
    rows = relationship(
        "ReportRunRow",
        backref="report_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, name, user, title, data):
        self.name = name

        if user is None:
            creator = ""
        else:
            if hasattr(user, "proxy_username"):
                creator = user.proxy_username
            else:
                creator = user.email_address
        self.creator = creator

        self.title = title
        self.date_created = utc_datetime_now()
        self.state = "running"
        self.update_data(data)

    def update(self, state):
        self.state = state

    def update_data(self, data):
        self.data = _jsonize(data)
        attributes.flag_modified(self, "data")

    def insert_row(self, sess, tab, titles, values, properties):
        vals = {"titles": titles, "values": values, "properties": properties}
        row = ReportRunRow(self, tab, vals)
        sess.add(row)

    def delete(self, sess):
        sess.delete(self)
        sess.flush()

    @staticmethod
    def insert(sess, name, user, title, data):
        report_run = ReportRun(name, user, title, data)
        sess.add(report_run)
        sess.flush()
        return report_run

    @staticmethod
    def w_update(report_run_id, state):
        with Session() as wsess:
            report_run = ReportRun.get_by_id(wsess, report_run_id)
            report_run.update(state)
            wsess.commit()

    @staticmethod
    def w_insert_row(report_run_id, tab, titles, values, properties):
        with Session() as wsess:
            report_run = ReportRun.get_by_id(wsess, report_run_id)
            report_run.insert_row(wsess, tab, titles, values, properties)
            wsess.commit()


def _jsonize(val):
    if isinstance(val, dict):
        d = {}
        for k, v in val.items():
            d[k] = _jsonize(v)
        return d

    elif isinstance(val, list):
        array = []
        for v in val:
            array.append(_jsonize(v))
        return array

    elif isinstance(val, Set):
        return [_jsonize(v) for v in sorted(val, key=str)[:3]]

    elif isinstance(val, Decimal):
        return float(val)

    elif isinstance(val, Datetime):
        return hh_format(val)

    else:
        return val


class ReportRunRow(Base, PersistentClass):
    __tablename__ = "report_run_row"
    id = Column(Integer, primary_key=True)
    report_run_id = Column(
        Integer,
        ForeignKey("report_run.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    tab = Column(String, nullable=False, index=True)
    data = Column(JSONB, nullable=False)

    def __init__(self, report_run, tab, data):
        self.report_run = report_run
        self.tab = tab
        self.data = _jsonize(data)


def read_file(pth, fname, attr):
    with open(os.path.join(pth, fname), "r") as f:
        contents = f.read()
    if attr is None:
        return loads(contents)
    else:
        return {attr: loads(contents)}


def insert_g_units(sess):
    for code, desc, factor_str in (
        ("MCUF", "Thousands of cubic feet", "28.3"),
        ("HCUF", "Hundreds of cubic feet", "2.83"),
        ("TCUF", "Tens of cubic feet", "0.283"),
        ("OCUF", "One cubic foot", "0.0283"),
        ("M3", "Cubic metres", "1"),
        ("HM3", "Hundreds of cubic metres", "100"),
        ("TM3", "Tens of cubic metres", "10"),
        ("NM3", "Tenths of cubic metres", "0.1"),
    ):
        GUnit.insert(sess, code, desc, Decimal(factor_str))


def insert_g_reading_frequencies(sess):
    for code, description in (("A", "Annual"), ("M", "Monthly")):
        GReadingFrequency.insert(sess, code, description)


def insert_bill_types(sess):
    for code, desc in (("F", "Final"), ("N", "Normal"), ("W", "Withdrawn")):
        BillType.insert(sess, code, desc)


def insert_energisation_statuses(sess):
    for code, desc in (("E", "Energised"), ("D", "De-Energised")):
        EnergisationStatus.insert(sess, code, desc)


def insert_g_read_types(sess):
    for code, desc in (
        ("A", "Actual"),
        ("C", "Customer"),
        ("E", "Estimated"),
        ("S", "Deemed read"),
    ):
        GReadType.insert(sess, code, desc)


def insert_cops(sess):
    for code, desc in (
        ("1", "CoP 1"),
        ("2", "CoP 2"),
        ("3", "CoP 3"),
        ("4", "CoP 4"),
        ("5", "CoP 5"),
        ("6a", "CoP 6a 20 day memory"),
        ("6b", "CoP 6b 100 day memory"),
        ("6c", "CoP 6c 250 day memory"),
        ("6d", "CoP 6d 450 day memory"),
        ("7", "CoP 7"),
        ("8", "CoP 8"),
        ("9", "CoP 9"),
        ("10", "CoP 10"),
        ("A", "CoP A"),
        ("B", "CoP B"),
        ("C", "CoP C"),
        ("D", "CoP D"),
        ("E", "CoP E"),
        ("F", "CoP F"),
        ("G", "CoP G"),
        ("H", "CoP H"),
        ("J", "CoP J"),
        ("K1", "CoP K1"),
        ("K2", "CoP K2"),
        ("N", "Where a dispensation applies or installation is not CoP compliant"),
    ):
        Cop.insert(sess, code, desc)


def insert_comms(sess):
    for code, desc in (
        ("IP", "Internet Protocol"),
        ("GSM", "Global System for Mobile Communications"),
        ("GPRS", "General Packet Radio Service"),
        ("PS", "Public Switch (BT Line)"),
        ("PK", "Paknet"),
        ("HP", "Handheld Perm"),
        ("SUB", "Sub Meter"),
    ):
        Comm.insert(sess, code, desc)


def insert_sources(sess):
    for code, desc in (
        ("net", "Public distribution system."),
        ("sub", "Sub meter"),
        ("gen-net", "Generator connected directly to network."),
        ("gen", "Generator."),
        ("3rd-party", "Third party supply."),
        ("3rd-party-reverse", "Third party supply with import going out of the site."),
    ):
        Source.insert(sess, code, desc)


def insert_generator_types(sess):
    for code, desc in (
        ("chp", "Combined heat and power."),
        ("lm", "Load management."),
        ("turb", "Water turbine."),
        ("pv", "Solar Photovoltaics."),
    ):
        sess.add(GeneratorType(code, desc))


def insert_voltage_levels(sess):
    for code, desc in (
        ("LV", "Low voltage"),
        ("HV", "High voltage"),
        ("EHV", "Extra high voltage"),
    ):
        VoltageLevel.insert(sess, code, desc)


def insert_dtc_meter_types(sess):
    for code, desc in (
        ("CHECK", "Check"),
        ("H", "Half Hourly"),
        ("K", "Key"),
        ("LAG_", "Lag"),
        ("LEAD_", "Lead"),
        ("MAIN_", "Main"),
        ("N", "Non-Half Hourly"),
        ("NCAMR", "Non-remotely Configurable Automated Meter Reading"),
        (
            "NSS",
            "A meter that meets the definition of an ADM but is not compliant with "
            "any version of SMETS",
        ),
        (
            "RCAMR",
            "Remotely Configurable Automated Meter Reading without remote "
            "enable/disable capability",
        ),
        (
            "RCAMY",
            "Remotely Configurable Automated Meter Reading with remote "
            "enable/disable capability",
        ),
        ("S", "Smartcard Prepayment"),
        (
            "S1",
            "A meter that is compliant with the Smart Metering Equipment Technical "
            "Specifications 1 (SMETS1)",
        ),
        ("S2A", "A single element meter that is compliant with SMETS2"),
        ("S2B", "A twin element meter that is compliant with SMETS2"),
        ("S2C", "A polyphase meter that is compliant with SMETS2"),
        (
            "S2AD",
            "A single element meter with one or more ALCS that is compliant with "
            "SMETS2",
        ),
        (
            "S2BD",
            "A twin element meter with one or more ALCS that is compliant with "
            "SMETS2",
        ),
        (
            "S2CDE",
            "A polyphase meter with one or more ALCS and Boost Function that is "
            "compliant with SMETS2",
        ),
        ("SPECL", "Special"),
        ("T", "Token"),
        (
            "2ADF",
            "Single Element with ALCS and Auxiliary Proportional Controller (APC) "
            "that is compliant with SMETS2",
        ),
        (
            "2ADEF",
            "Single Element with ALCS, Boost Function and APC that is compliant "
            "with SMETS2",
        ),
        (
            "2AEF",
            "Single Element with Boost Function and APC that is compliant with SMETS2",
        ),
        ("2AF", "Single Element with APC that is compliant with SMETS2"),
        ("2BF", "Twin Element with APC that is compliant with SMETS2"),
        ("2BDF", "Twin Element with ALCS and APC that is compliant with SMETS2"),
        (
            "2BDEF",
            "Twin Element with ALCS, Boost Function and APC that is compliant with "
            "SMETS2",
        ),
        (
            "2BEF",
            "Twin Element with Boost Function and APC that is compliant with SMETS2",
        ),
        (
            "2CDEF",
            "Polyphase with ALCS, Boost Function and APC that is compliant with SMETS2",
        ),
        ("2CF", "Polyphase with APC that is compliant with SMETS2"),
        ("2CDF", "Polyphase with ALCS and APC that is compliant with SMETS2"),
        ("2CEF", "Polyphase with Boost Function and APC that is compliant with SMETS2"),
        (
            "S2ADE",
            "Single element meter with one or more ALCS and Boost Function that is "
            "compliant with SMETS2",
        ),
        (
            "S2BDE",
            "A twin element meter with one or more ALCS and Boost Function that is "
            "compliant with SMETS2",
        ),
        (
            "S2CD",
            "A polyphase meter with one or more ALCS that is compliant with SMETS2",
        ),
    ):
        DtcMeterType.insert(sess, code, desc)


def insert_read_types(sess):
    for code, desc in (
        ("A", "Actual Change of Supplier Read"),
        ("D", "Deemed (Settlement Registers) or Estimated (Non-Settlement Registers)"),
        ("C", "Customer"),
        ("CP", "Computer"),
        ("E", "Estimated"),
        ("E3", "Estimated 3rd Party"),
        ("EM", "Estimated Manual"),
        ("F", "Final"),
        ("H", "Data Collector Reading Queried By Supplier"),
        ("I", "Initial"),
        ("IF", "Information"),
        ("N", "Normal"),
        ("N3", "Normal 3rd Party"),
        ("O", "Old Supplier's Estimated CoS Reading"),
        ("Q", "Meter Reading modified manually by DC"),
        ("S", "Special"),
        ("W", "Withdrawn"),
        ("X", "Exchange"),
        ("Z", "Actual Change of Tenancy Read"),
    ):
        sess.add(ReadType(code, desc))


def db_init(sess, root_path):
    db_name = config["PGDATABASE"]
    log_message("Initializing database.")

    ct_now = ct_datetime_now()
    last_month_start, _ = list(
        c_months_u(finish_year=ct_now.year, finish_month=ct_now.month, months=2)
    )[0]

    insert_voltage_levels(sess)
    sess.commit()

    for code in ("editor", "viewer", "party-viewer"):
        UserRole.insert(sess, code)
    sess.commit()

    insert_sources(sess)
    sess.commit()

    insert_generator_types(sess)
    sess.commit()

    insert_read_types(sess)
    sess.commit()

    insert_cops(sess)
    sess.commit()

    insert_comms(sess)
    sess.commit()

    insert_bill_types(sess)
    sess.commit()

    insert_energisation_statuses(sess)
    sess.commit()

    Pc.insert(sess, "00", "Half-hourly", to_utc(ct_datetime(1996, 4, 1)), None)
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core Role")
    participant = Participant.insert(sess, "CALB", "Coopers & Lybrand")
    participant.insert_party(
        sess,
        market_role_Z,
        "1 Embankment Place",
        to_utc(ct_datetime(1996, 4, 1)),
        None,
        None,
    )
    for name, properties in (
        ("aahedc", {}),
        (
            "bank_holidays",
            {
                "enabled": True,
                "url": "https://www.gov.uk/bank-holidays/england-and-wales.ics",
            },
        ),
        ("bmarketidx", {}),
        ("bsuos", {}),
        ("ccl", {}),
        ("configuration", {}),
        ("rcrc", {}),
        ("ro", {}),
        ("system_price", {}),
        ("tlms", {}),
        ("triad_dates", {}),
        ("tnuos", {}),
    ):
        Contract.insert_non_core(sess, name, "", properties, last_month_start, None, {})

    insert_dtc_meter_types(sess)
    sess.commit()

    insert_g_read_types(sess)
    sess.commit()

    insert_g_units(sess)
    sess.commit()

    for code, name in (
        ("EE", "East of England"),
        ("LO", "London"),
        ("NW", "North West"),
        ("WM", "West Midlands"),
        ("SC", "Scotland"),
        ("SO", "Southern"),
        ("NO", "Northern"),
        ("WW", "Wales & West"),
    ):
        GDn.insert(sess, code, name)
    sess.commit()
    sess.flush()

    dns = {
        "EE": {"EA": ["EA1", "EA2", "EA3", "EA4"], "EM": ["EM1", "EM2", "EM3", "EM4"]},
        "LO": {"NT": ["NT1", "NT2", "NT3"]},
        "NW": {"NW": ["NW1", "NW2"]},
        "WM": {"WM": ["WM1", "WM2", "WM3"]},
        "SC": {
            "LC": ["LC"],
            "LO": ["LO"],
            "LS": ["LS"],
            "LT": ["LT"],
            "LW": ["LW"],
            "SC": ["SC1", "SC2", "SC4"],
        },
        "SO": {"SE": ["SE1", "SE2"], "SO": ["SO1", "SO2"]},
        "NO": {"NE": ["NE1", "NE2", "NE3"], "NO": ["NO1", "NO2"]},
        "WW": {"SW": ["SW1", "SW2", "SW3"], "WN": ["WA1"], "WS": ["WA2"]},
    }
    for dn_code, dn in sorted(dns.items()):
        g_dn = GDn.get_by_code(sess, dn_code)
        for ldz_code, exit_zone_codes in sorted(dn.items()):
            g_ldz = g_dn.insert_g_ldz(sess, ldz_code)
            for exit_zone_code in exit_zone_codes:
                g_ldz.insert_g_exit_zone(sess, exit_zone_code)
    sess.commit()

    for code, description in (("A", "Annual"), ("M", "Monthly")):
        sess.add(GReadingFrequency(code, description))
    sess.commit()
    sess.flush()

    for name, props, rs in (
        ("ccl", {}, {}),
        (
            "cv",
            {
                "enabled": True,
                "url": "http://mip-prd-web.azurewebsites.net/DataItemViewer/"
                "DownloadFile",
            },
            {},
        ),
        ("dn", {}, {}),
        (
            "ug",
            {},
            {
                "ug_gbp_per_kwh": {
                    "EA1": 0,
                    "EA2": 0,
                    "EA3": 0,
                    "EA4": 0,
                    "EM1": 0,
                    "EM2": 0,
                    "EM3": 0,
                    "EM4": 0,
                    "LC": 0,
                    "LO": 0,
                    "LS": 0,
                    "LT": 0,
                    "LW": 0,
                    "NE1": 0,
                    "NE2": 0,
                    "NE3": 0,
                    "NO1": 0,
                    "NO2": 0,
                    "NT1": 0,
                    "NT2": 0,
                    "NT3": 0,
                    "NW1": 0,
                    "NW2": 0,
                    "SC1": 0,
                    "SC2": 0,
                    "SC4": 0,
                    "SE1": 0,
                    "SE2": 0,
                    "SO1": 0,
                    "SO2": 0,
                    "SW1": 0,
                    "SW2": 0,
                    "SW3": 0,
                    "WA1": 0,
                    "WA2": 0,
                    "WM1": 0,
                    "WM2": 0,
                    "WM3": 0,
                },
            },
        ),
        ("nts_commodity", {}, {}),
    ):
        GContract.insert_industry(sess, name, "", props, last_month_start, None, rs)

    sess.execute(
        text(f'alter database "{db_name}" set default_transaction_deferrable = on')
    )
    sess.execute(text(f"""alter database "{db_name}" SET DateStyle TO 'ISO, YMD'"""))
    sess.commit()
    sess.close()
    engine.dispose()

    # Check the transaction isolation level is serializable
    isolation_level = sess.execute(text("show transaction isolation level")).scalar()
    if isolation_level != "serializable":
        raise Exception(
            f"The transaction isolation level for database {db_name} should be "
            f"'serializable' but in fact it's {isolation_level}."
        )

    conf = (
        sess.query(Contract)
        .join(MarketRole)
        .filter(Contract.name == "configuration", MarketRole.code == "Z")
        .one()
    )
    state = conf.make_state()
    new_state = dict(state)
    new_state["db_version"] = len(upgrade_funcs)
    conf.update_state(new_state)
    sess.commit()


def db_upgrade_18_to_19(sess, root_path):
    for code, factor in (
        ("MCUF", "28.3"),
        ("HCUF", "2.83"),
        ("TCUF", "0.283"),
        ("OCUF", "0.0283"),
    ):
        g_unit = sess.query(GUnit).filter(GUnit.code == code).one()
        g_unit.factor = Decimal(factor)


def db_upgrade_19_to_20(sess, root_path):
    for code, description in (("A", "Annual"), ("M", "Monthly")):
        sess.add(GReadingFrequency(code, description))
    sess.flush()

    sess.execute(
        "alter table g_era "
        "add g_reading_frequency_id integer "
        "references g_reading_frequency (id);"
    )
    sess.execute(
        "update g_era set g_reading_frequency_id = "
        "(select id from g_reading_frequency where code = 'A');"
    )
    sess.execute("alter table g_era alter g_reading_frequency_id set not null;")


def db_upgrade_20_to_21(sess, root_path):
    market_role_id = sess.execute(
        "select id from market_role where code = 'Z'"
    ).fetchone()[0]
    sess.execute(
        "update contract set charge_script = '' where "
        "market_role_id = :market_role_id and name = 'bsuos';",
        {"market_role_id": market_role_id},
    )


def db_upgrade_21_to_22(sess, root_path):
    for code, desc in (
        ("A", "Actual Change of Supplier Read"),
        (
            "D",
            "Deemed (Settlement Registers) or Estimated (Non-Settlement " "Registers)",
        ),
        ("F", "Final"),
        ("H", "Data Collector Reading Queried By Supplier"),
        ("I", "Initial"),
        ("O", "Old Supplier's Estimated CoS Reading"),
        ("Q", "Meter Reading modified manually by DC"),
        ("S", "Special"),
        ("Z", "Actual Change of Tenancy Read"),
    ):
        sess.add(ReadType(code, desc))


def db_upgrade_22_to_23(sess, root_path):
    sess.execute("alter table g_ldz alter g_dn_id set not null;")
    sess.execute("alter table g_exit_zone alter g_ldz_id set not null;")


def db_upgrade_23_to_24(sess, root_path):
    Contract.insert_non_core(
        sess,
        "bmarketidx",
        "",
        {},
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 1),
        {},
    )


def db_upgrade_24_to_25(sess, root_path):
    insert_energisation_statuses(sess)
    sess.execute(
        "alter table era "
        "add energisation_status_id integer "
        "references energisation_status (id);"
    )
    es_id = sess.execute("select id from energisation_status where code = 'E'").scalar()
    sess.execute(
        "update era set energisation_status_id = :es_id", params={"es_id": es_id}
    )
    sess.execute("alter table era alter energisation_status_id set not null;")


def db_upgrade_25_to_26(sess, root_path):
    for mtc_id, mtc_meter_type_id in sess.execute(
        "select id, meter_type_id from mtc order by id"
    ):
        meter_type_code = sess.execute(
            "select code from meter_type where id = :id",
            params={"id": mtc_meter_type_id},
        ).scalar()
        new_meter_type_id = sess.execute(
            "select id from meter_type where code = :code order by id desc",
            params={"code": meter_type_code},
        ).first()[0]
        sess.execute(
            "update mtc set meter_type_id = :meter_type_id where id = :id",
            params={"id": mtc_id, "meter_type_id": new_meter_type_id},
        )

    meter_type_codes = set()
    for (meter_type_code,) in sess.execute("select code from meter_type"):
        meter_type_codes.add(meter_type_code)

    for code in meter_type_codes:
        code_id = sess.execute(
            "select id from meter_type where code = :code order by id",
            params={"code": code},
        ).first()[0]
        sess.execute("delete from meter_type where id = :id", params={"id": code_id})


def db_upgrade_26_to_27(sess, root_path):
    party_88 = sess.execute(select(Party).where(Party.dno_code == "88")).scalar_one()
    participant_cidc = sess.execute(
        select(Participant).where(Participant.code == "CIDC")
    ).scalar_one()
    party_88.participant = participant_cidc


def db_upgrade_27_to_28(sess, root_path):
    insert_comms(sess)
    sess.execute("alter table era add comm_id integer references comm (id);")
    for era in sess.execute(select(Era).order_by(Era.id)).scalars():
        props = era.props
        try:
            code = props["comms_type"]
            del props["comms_type"]
            era.properties = dumps(props)
        except KeyError:
            code = "GSM"
        era.comm = Comm.get_by_code(sess, code.upper())
        sess.flush()


def db_upgrade_28_to_29(sess, root_path):
    sess.execute("ALTER TABLE report_run ADD data JSONB;")
    sess.execute("UPDATE report_run SET data = CAST('{}' as JSONB)")
    sess.execute("ALTER TABLE report_run ALTER data SET NOT NULL;")


def db_upgrade_29_to_30(sess, root_path):
    val = sess.execute("select max(id) from ssc;").scalar_one()
    sess.execute("select setval('ssc_id_seq', :val)", {"val": val})


def db_upgrade_30_to_31(sess, root_path):
    sess.execute("ALTER TABLE ssc DROP CONSTRAINT IF EXISTS ssc_code_key")


def db_upgrade_31_to_32(sess, root_path):
    sess.execute("alter table era add old_mtc_id integer references old_mtc (id);")
    for era_id, mtc_dno_id, mtc_code, mtc_valid_from in sess.execute(
        "select era.id, mtc.dno_id, mtc.code, mtc.valid_from "
        "from era, mtc where era.mtc_id = mtc.id"
    ):
        params = {
            "code": mtc_code,
            "valid_from": to_utc(mtc_valid_from),
        }
        if mtc_dno_id is None:
            q = (
                "select id from old_mtc "
                "where dno_id is null and code = :code and valid_from = :valid_from"
            )
        else:
            params["dno_id"] = mtc_dno_id
            q = (
                "select id from old_mtc "
                "where dno_id = :dno_id and code = :code and valid_from = :valid_from"
            )
        old_mtc_id = sess.execute(q, params=params).scalar_one()
        sess.execute(
            "UPDATE era SET old_mtc_id = :old_mtc_id where id = :era_id",
            params={"old_mtc_id": old_mtc_id, "era_id": era_id},
        )
    sess.execute("alter table era alter old_mtc_id set not null;")


def db_upgrade_32_to_33(sess, root_path):
    sess.execute("ALTER TABLE era DROP mtc_id CASCADE;")
    sess.execute("DROP TABLE valid_mtc_llfc_ssc_pc CASCADE;")
    sess.execute("DROP TABLE mtc CASCADE;")


def db_upgrade_33_to_34(sess, root_path):
    contract = Contract.insert_non_core(
        sess,
        "ro",
        "",
        {},
        to_utc(ct_datetime(2000, 4, 1)),
        None,
        {"ro_gbp_per_msp_kwh": 0.00},
    )
    for year, script in [
        (2015, {"ro_gbp_per_msp_kwh": 0.0128557}),
        (2016, {"ro_gbp_per_msp_kwh": 0.01557996}),
        (2017, {"ro_gbp_per_msp_kwh": 0.01864}),
        (2018, {"ro_gbp_per_msp_kwh": 0.02245896}),
        (2019, {"ro_gbp_per_msp_kwh": 0.02374052}),
        (2020, {"ro_gbp_per_msp_kwh": 0.02447467}),
        (2021, {"ro_gbp_per_msp_kwh": 0.0249936}),
        (2022, {"ro_gbp_per_msp_kwh": 0.02596408}),
    ]:
        contract.insert_rate_script(sess, to_utc(ct_datetime(year, 4, 1)), script)


def db_upgrade_34_to_35(sess, root_path):
    valid_from = utc_datetime(2000, 1, 1)
    mtc_845 = Mtc.get_by_code(sess, "845", valid_from)
    mtc_801 = Mtc.get_by_code(sess, "801", valid_from)
    meter_type_c5 = MeterType.get_by_code(sess, "C5", valid_from)
    meter_type_un = MeterType.get_by_code(sess, "UN", valid_from)
    meter_payment_type_cr = MeterPaymentType.get_by_code(sess, "CR", valid_from)
    participant_cidc = Participant.get_by_code(sess, "CIDC")
    participant_crow = Participant.get_by_code(sess, "CROW")

    MtcParticipant.insert(
        sess,
        mtc_845,
        participant_cidc,
        "HH COP5 And Above With Comms",
        True,
        True,
        meter_type_c5,
        meter_payment_type_cr,
        None,
        to_utc(ct_datetime(1996, 4, 1)),
        None,
    )
    MtcParticipant.insert(
        sess,
        mtc_845,
        participant_crow,
        "HH COP5 And Above With Comms",
        True,
        True,
        meter_type_c5,
        meter_payment_type_cr,
        None,
        to_utc(ct_datetime(1996, 4, 1)),
        None,
    )
    MtcParticipant.insert(
        sess,
        mtc_801,
        participant_crow,
        "NHH Unrestricted 1-rate Non-Prog Credit Meter",
        True,
        False,
        meter_type_un,
        meter_payment_type_cr,
        None,
        to_utc(ct_datetime(1996, 4, 1)),
        None,
    )

    sess.execute(
        "alter table era "
        "add mtc_participant_id integer references mtc_participant (id);"
    )
    for era_id, supply_id, old_mtc_code, old_mtc_valid_from in sess.execute(
        "select era.id, era.supply_id, old_mtc.code, old_mtc.valid_from "
        "from era, old_mtc where era.old_mtc_id = old_mtc.id"
    ):
        supply = Supply.get_by_id(sess, supply_id)
        mtc = sess.execute(
            select(Mtc)
            .where(Mtc.code == old_mtc_code, Mtc.valid_from <= old_mtc_valid_from)
            .order_by(Mtc.valid_from.desc())
        ).scalar()
        mtc_participant = sess.execute(
            select(MtcParticipant)
            .where(
                MtcParticipant.participant == supply.dno.participant,
                MtcParticipant.mtc == mtc,
                MtcParticipant.valid_from >= mtc.valid_from,
            )
            .order_by(MtcParticipant.valid_from.desc())
        ).scalar()
        sess.execute(
            "UPDATE era SET mtc_participant_id = :mtc_participant_id "
            "where id = :era_id",
            params={"mtc_participant_id": mtc_participant.id, "era_id": era_id},
        )
    sess.execute("alter table era alter mtc_participant_id set not null;")


def db_upgrade_35_to_36(sess, root_path):
    sess.execute("ALTER TABLE era DROP old_mtc_id CASCADE;")
    sess.execute("DROP TABLE old_valid_mtc_llfc_ssc_pc CASCADE;")
    sess.execute("DROP TABLE old_mtc CASCADE;")


def db_upgrade_36_to_37(sess, root_path):
    """
    for dno in (
        sess.query(Party)
        .join(MarketRole)
        .filter(MarketRole.code == "R")
        .order_by(Party.dno_code)
    ):
        scripts = get_file_scripts(dno.dno_code)
        contract = Contract.find_dno_by_name(sess, dno.dno_code)
        if contract is None:
            contract = Contract.insert_dno(
                sess,
                dno.dno_code,
                dno.participant,
                "",
                {},
                scripts[0][0],
                None,
                loads(scripts[0][2]),
            )
        for script in scripts[1:]:
            contract.insert_rate_script(sess, script[0], loads(script[2]))
    """


def db_upgrade_37_to_38(sess, root_path):
    """
    sess.execute("ALTER TABLE g_contract ADD is_industry boolean;")
    sess.execute("UPDATE g_contract SET is_industry = false;")

    sess.execute("ALTER TABLE g_contract ALTER is_industry SET NOT NULL;")
    sess.execute("ALTER TABLE g_contract ADD UNIQUE (is_industry, name);")

    for name in ("g_dn", "g_ccl", "g_ug", "g_nts_commodity"):
        scripts = get_file_scripts(name)
        g_contract = GContract.insert(
            sess, True, name[2:], "", {}, scripts[0][0], None, loads(scripts[0][2])
        )
        for script in scripts[1:]:
            g_contract.insert_g_rate_script(sess, script[0], loads(script[2]))

    old_cv_contract = Contract.get_non_core_by_name(sess, "g_cv")
    rsl = list(
        sess.execute(
            select(RateScript)
            .where(RateScript.contract == old_cv_contract)
            .order_by(RateScript.start_date)
        ).scalars()
    )

    cv_contract = GContract.insert(
        sess,
        True,
        "cv",
        old_cv_contract.charge_script,
        old_cv_contract.make_properties(),
        rsl[0].start_date,
        rsl[-1].finish_date,
        loads(rsl[0].script),
    )
    for rs in rsl[1:]:
        cv_contract.insert_g_rate_script(sess, rs.start_date, loads(rs.script))
    """


def db_upgrade_38_to_39(sess, root_path):
    """
    for name in ("aahedc", "ccl", "triad_dates", "triad_rates"):
        scripts = get_file_scripts(name)
        contract = Contract.insert_non_core(
            sess, name, "", {}, scripts[0][0], None, loads(scripts[0][2])
        )
        for script in scripts[1:]:
            contract.insert_rate_script(sess, script[0], loads(script[2]))
    """


def db_upgrade_39_to_40(sess, root_path):
    contract = Contract.get_non_core_by_name(sess, "triad_rates")
    contract.name = "tnuos"


def db_upgrade_40_to_41(sess, root_path):
    val = sess.execute("select max(id) from tpr;").scalar_one()
    sess.execute("select setval('tpr_id_seq', :val)", {"val": val})

    val = sess.execute("select max(id) from clock_interval;").scalar_one()
    sess.execute("select setval('clock_interval_id_seq', :val)", {"val": val})

    val = sess.execute("select max(id) from measurement_requirement;").scalar_one()
    sess.execute("select setval('measurement_requirement_id_seq', :val)", {"val": val})


def db_upgrade_41_to_42(sess, root_path):
    for code, desc in (
        ("8", "CoP 8"),
        ("9", "CoP 9"),
        ("10", "CoP 10"),
        ("A", "CoP A"),
        ("B", "CoP B"),
        ("C", "CoP C"),
        ("D", "CoP D"),
        ("E", "CoP E"),
        ("F", "CoP F"),
        ("G", "CoP G"),
        ("H", "CoP H"),
        ("J", "CoP J"),
        ("K1", "CoP K1"),
        ("K2", "CoP K2"),
        ("N", "Where a dispensation applies or installation is not CoP compliant"),
    ):
        Cop.insert(sess, code, desc)


def db_upgrade_42_to_43(sess, root_path):
    for supply in sess.execute(select(Supply).order_by(Supply.id)).scalars():
        supply_note = supply.note
        if len(supply_note.strip()) > 0:
            note = literal_eval(supply_note)
            supply.note = dumps(note)
            sess.commit()


def db_upgrade_43_to_44(sess, root_path):
    dups = {}
    for read in sess.scalars(select(RegisterRead)):
        k = (
            read.bill_id,
            read.msn,
            read.mpan_str,
            read.coefficient,
            read.units,
            read.tpr_id,
            read.previous_date,
            read.previous_value,
            read.previous_type_id,
            read.present_date,
            read.present_value,
            read.present_type_id,
        )
        if k in dups:
            dups[k].append(read.id)
        else:
            dups[k] = []

    for read_ids in dups.values():
        for read_id in read_ids:
            read = RegisterRead.get_by_id(sess, read_id)
            read.delete(sess)

    sess.execute(
        text(
            """ALTER TABLE register_read ADD CONSTRAINT
            register_read_bill_id_msn_mpan_str_coefficient_units_tpr_id_key UNIQUE (
            bill_id,
            msn,
            mpan_str,
            coefficient,
            units,
            tpr_id,
            previous_date,
            previous_value,
            previous_type_id,
            present_date,
            present_value,
            present_type_id
        );"""
        )
    )


def db_upgrade_44_to_45(sess, root_path):
    sess.execute(text("ALTER TABLE g_era ADD aq NUMERIC;"))
    sess.execute(text("ALTER TABLE g_era ADD soq NUMERIC;"))
    sess.execute(text("UPDATE g_era SET aq = 0"))
    sess.execute(text("UPDATE g_era SET soq = 0"))
    sess.execute(text("ALTER TABLE g_era ALTER aq SET NOT NULL;"))
    sess.execute(text("ALTER TABLE g_era ALTER soq SET NOT NULL;"))


def db_upgrade_45_to_46(sess, root_path):
    sess.execute(
        text(
            "ALTER TABLE batch DROP CONSTRAINT IF EXISTS "
            "batch_contract_id_reference_key;"
        )
    )
    sess.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS batch_reference_key ON batch "
            "(reference);"
        )
    )


def db_upgrade_46_to_47(sess, root_path):
    insert_dtc_meter_types(sess)
    sess.flush()

    sess.execute(
        text(
            "alter table era add dtc_meter_type_id integer references dtc_meter_type "
            "(id);"
        )
    )
    for era_id, pc_id, era_properties, mtc_participant_id in sess.execute(
        text("select era.id, era.pc_id, era.properties, mtc_participant_id from era")
    ):
        dtc_meter_type_id = None
        props = loads(era_properties)
        if "meter_type" in props:
            mt_code = props["meter_type"]
            dtc_meter_type = DtcMeterType.find_by_code(sess, mt_code)
            if dtc_meter_type is not None:
                dtc_meter_type_id = dtc_meter_type.id

        if dtc_meter_type_id is None:
            mtc_participant = MtcParticipant.get_by_id(sess, mtc_participant_id)
            if mtc_participant.meter_type.code not in ["UM", "PH"]:
                pc = Pc.get_by_id(sess, pc_id)
                if pc.code == "00":
                    dtc_meter_type_code = "H"
                else:
                    channels = sess.scalars(
                        select(Channel).where(Channel.era_id == era_id)
                    ).all()
                    if len(channels) > 0:
                        dtc_meter_type_code = "RCAMR"
                    else:
                        dtc_meter_type_code = "N"
                dtc_meter_type = DtcMeterType.get_by_code(sess, dtc_meter_type_code)
                dtc_meter_type_id = dtc_meter_type.id

        sess.execute(
            text(
                "UPDATE era SET dtc_meter_type_id = :dtc_meter_type_id "
                "where id = :era_id"
            ),
            params={"dtc_meter_type_id": dtc_meter_type_id, "era_id": era_id},
        )
    sess.execute(text("alter table era drop column properties;"))


def db_upgrade_47_to_48(sess, root_path):
    for code, desc in (
        (
            "S2ADE",
            "Single element meter with one or more ALCS and Boost Function that is "
            "compliant with SMETS2",
        ),
        (
            "S2BDE",
            "A twin element meter with one or more ALCS and Boost Function that is "
            "compliant with SMETS2",
        ),
        (
            "S2CD",
            "A polyphase meter with one or more ALCS that is compliant with SMETS2",
        ),
    ):
        DtcMeterType.insert(sess, code, desc)


def db_upgrade_48_to_49(sess, root_path):
    for code, factor_str in (
        ("MCUF", "28.316846592"),
        ("HCUF", "2.8316846592"),
        ("TCUF", "0.28316846592"),
        ("OCUF", "0.028316846592"),
    ):
        g_unit = GUnit.get_by_code(sess, code)
        g_unit.factor = Decimal(factor_str)
        sess.flush()


upgrade_funcs = [None] * 18
upgrade_funcs.extend(
    [
        db_upgrade_18_to_19,
        db_upgrade_19_to_20,
        db_upgrade_20_to_21,
        db_upgrade_21_to_22,
        db_upgrade_22_to_23,
        db_upgrade_23_to_24,
        db_upgrade_24_to_25,
        db_upgrade_25_to_26,
        db_upgrade_26_to_27,
        db_upgrade_27_to_28,
        db_upgrade_28_to_29,
        db_upgrade_29_to_30,
        db_upgrade_30_to_31,
        db_upgrade_31_to_32,
        db_upgrade_32_to_33,
        db_upgrade_33_to_34,
        db_upgrade_34_to_35,
        db_upgrade_35_to_36,
        db_upgrade_36_to_37,
        db_upgrade_37_to_38,
        db_upgrade_38_to_39,
        db_upgrade_39_to_40,
        db_upgrade_40_to_41,
        db_upgrade_41_to_42,
        db_upgrade_42_to_43,
        db_upgrade_43_to_44,
        db_upgrade_44_to_45,
        db_upgrade_45_to_46,
        db_upgrade_46_to_47,
        db_upgrade_47_to_48,
        db_upgrade_48_to_49,
    ]
)


def db_upgrade(root_path):
    with Session() as sess:
        db_version = find_db_version(sess)
        curr_version = len(upgrade_funcs)
        if db_version is None:
            log_message("It looks like the chellow database hasn't been initialized.")
            db_init(sess, root_path)
        elif db_version == curr_version:
            log_message(
                f"The database version is {db_version} and the latest version is "
                f"{curr_version} so it doesn't look like you need to run an upgrade."
            )
        elif db_version > curr_version:
            log_message(
                f"The database version is {db_version} and the latest database "
                f"version is {curr_version} so it looks like you're using an old "
                f"version of Chellow."
            )
        else:
            log_message(
                f"Upgrading from database version {db_version} to database version "
                f"{db_version + 1}."
            )
            upgrade_funcs[db_version](sess, root_path)
            conf = (
                sess.query(Contract)
                .join(MarketRole)
                .filter(Contract.name == "configuration", MarketRole.code == "Z")
                .one()
            )
            state = conf.make_state()
            state["db_version"] = db_version + 1
            conf.update_state(state)
            sess.commit()
            log_message(
                f"Successfully upgraded from database version {db_version} to "
                f"database version {db_version + 1}."
            )


def find_db_version(sess):
    conf = (
        sess.query(Contract)
        .join(MarketRole)
        .filter(Contract.name == "configuration", MarketRole.code == "Z")
        .first()
    )
    if conf is None:
        return None
    conf_state = loads(conf.state)
    return conf_state.get("db_version", 0)
