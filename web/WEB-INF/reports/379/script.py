from net.sf.chellow.monad import Monad
import db
import templater
import utils
from sqlalchemy.exc import SQLAlchemyError

Monad.getUtils()['impt'](globals(), 'templater', 'db', 'utils')
form_str = utils.form_str
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    result = None
    messages = None
    if inv.hasParameter('query'):
        query = form_str(inv, 'query')
        query = query.strip()
        if len(query) > 0:
            try:
                result = sess.execute(query)
            except SQLAlchemyError, e:
                messages = [str(e)]

    templater.render(inv, template, {'result': result, 'messages': messages})
finally:
    if sess is not None:
        sess.close()
