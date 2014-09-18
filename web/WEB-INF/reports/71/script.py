from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'Participant', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    participants = sess.query(Participant).from_statement("select * from participant order by participant.code").all()
    render(inv, template, {'participants': participants})
finally:
    sess.close()