from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    parties = sess.query(Party).from_statement("select party.* from party, market_role where party.market_role_id = market_role.id order by party.name, market_role.code").all()
    render(inv, template, {'parties': parties})
finally:
    sess.close()