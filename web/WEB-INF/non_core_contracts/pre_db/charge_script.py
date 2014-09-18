from sqlalchemy import Column, Integer, DateTime, Boolean, String, create_engine, ForeignKey, Sequence
from net.sf.chellow.monad import Monad, Hiber
from sqlalchemy.orm import relationship, backref, sessionmaker, _mapper_registry
from sqlalchemy.ext.declarative import declarative_base
from javax.management import MBeanServerFactory, ObjectName

_mapper_registry.clear()

Monad.getUtils()['imprt'](globals(), {
        'utils': ['UserException', 'NotFoundException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH']})

# Get db name
con = Hiber.session().connection()
stmt = con.createStatement()
rs = stmt.executeQuery("select current_database()")
while rs.next():
    db_name = str(rs.getString("current_database"))
Hiber.close()

def set_read_write(sess):
    sess.execute("rollback")
    sess.execute("set transaction isolation level serializable read write")

ctx = Monad.getContext()
username = ctx.getInitParameter('db.username')
password = ctx.getInitParameter('db.password')

# get db hostname

server_list = MBeanServerFactory.findMBeanServer(None)
server = server_list[0]
beans = server.queryNames(ObjectName('Catalina:type=DataSource,context=/chellow,class=javax.sql.DataSource,name="jdbc/chellow",*'), None)
bean = beans.toArray()[0]

try:
    attrs = server.getAttributes(bean, ['url'])


    url = str(attrs[0])

    i = url.find("//")
    url = url[i + 2:]
    i = url.find(":")
    hostname = url[:i]
except IndexError:
    for attr in str(bean).split(","):
        if attr.startswith("host="):
            hostname = attr[5:]

con_str = "postgresql+pg8000://" + username + ":" + password + "@" + hostname + "/" + db_name

engine = create_engine(con_str.encode('ascii'), isolation_level="SERIALIZABLE")

Session = sessionmaker(bind=engine)

Base = declarative_base()


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

class VoltageLevel(Base, PersistentClass):

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


class GeneratorType(Base, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        gen_type = sess.query(GeneratorType).filter_by(code=code).first()
        if gen_type is None:
            raise UserException("There's no generator type with the code '"
                    + code + "'")
        return gen_type

    __tablename__ = 'generator_type'
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    supplies = relationship('Supply', backref='generator_type')

class Source(Base, PersistentClass):
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
    
class GspGroup(Base, PersistentClass):
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