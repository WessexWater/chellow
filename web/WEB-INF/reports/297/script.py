from net.sf.chellow.monad import Monad

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Site', 'set_read_write'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH'],
        'templater': ['render']})


def make_fields(sess, message=None):
        messages = [] if message is None else [str(e)]
        return {'messages': messages}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        render(inv, template, make_fields(sess))
    else:
        set_read_write(sess)
        code = inv.getString("code")
        name = inv.getString("name")
        site = Site.insert(sess, code, name)
        sess.commit()
        inv.sendSeeOther("/reports/5/output/?site_id=" + str(site.id))
except UserException, e:
    render(inv, template, make_fields(sess, e))
finally:
    if sess is not None:
        sess.close()