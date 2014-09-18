from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'Participant', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    participant_id = inv.getLong('participant_id')
    participant = Participant.get_by_id(sess, participant_id)
    render(inv, template, {'participant': participant})
finally:
    sess.close()