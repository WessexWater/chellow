from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Party = db.Party
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    party_id = inv.getLong('party_id')
    party = Party.get_by_id(sess, party_id)
    render(inv, template, {'party': party})
finally:
    if sess is not None:
        sess.close()
