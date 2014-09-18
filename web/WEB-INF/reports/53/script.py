from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'templater', 'db')
Pc = db.Pc

sess = None
try:
    sess = db.session()
    pcs = sess.query(Pc).order_by(Pc.code)
    templater.render(inv, template, {'pcs': pcs})
finally:
    if sess is not None:
        sess.close()