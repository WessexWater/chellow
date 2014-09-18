from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'templater', 'db')

sess = None
try:
    sess = db.session()
    config = db.Contract.get_non_core_by_name(sess, 'configuration')
    templater.render(inv, template, {'properties': config.make_properties()})
finally:
    if sess is not None:
        sess.close()