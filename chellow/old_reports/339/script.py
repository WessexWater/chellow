from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
Source = db.Source
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    source_id = inv.getLong('source_id')
    source = Source.get_by_id(sess, source_id)
    render(inv, template, {'source': source})
finally:
    if sess is not None:
        sess.close()
