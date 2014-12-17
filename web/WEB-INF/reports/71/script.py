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
    participants = sess.query(Participant).order_by(Participant.code).all()
    render(inv, template, {'participants': participants})
finally:
    if sess is not None:
        sess.close()
