from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Participant = db.Participant
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    participant_id = inv.getLong('participant_id')
    participant = Participant.get_by_id(sess, participant_id)
    render(inv, template, {'participant': participant})
finally:
    sess.close()
