from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'templater', 'db')
Cop = db.Cop

sess = None
try:
    sess = db.session()
    cops = sess.query(Cop).order_by(Cop.code)
    templater.render(inv, template, {'cops': cops})
finally:
    if sess is not None:
        sess.close()