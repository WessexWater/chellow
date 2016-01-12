from net.sf.chellow.monad import Monad
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
inv, template = globals()['inv'], globals()['template']


def make_fields(hh, message=None):
    messages = [] if message is None else [str(message)]
    return {'hh': hh, 'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        hh_id = inv.getLong('hh_datum_id')
        hh = db.HhDatum.get_by_id(sess, hh_id)
        templater.render(inv, template, make_fields(hh))
    else:
        db.set_read_write(sess)
        hh_id = inv.getLong('hh_datum_id')
        hh = db.HhDatum.get_by_id(sess, hh_id)
        channel_id = hh.channel.id
        if inv.hasParameter('delete'):
            hh.channel.delete_data(sess, hh.start_date, hh.start_date)
            sess.commit()
            inv.sendSeeOther(
                '/reports/301/output/?channel_id=' + str(channel_id))
        else:
            value = utils.form_decimal(inv, 'value')
            status = inv.getString('status')
            channel = hh.channel
            era = channel.era
            imp_mpan_core = era.imp_mpan_core
            exp_mpan_core = era.exp_mpan_core
            mpan_core = imp_mpan_core if channel.imp_related else exp_mpan_core
            db.HhDatum.insert(
                sess, [
                    {
                        'mpan_core': mpan_core,
                        'channel_type': channel.channel_type,
                        'start_date': hh.start_date, 'value': value,
                        'status': status}])
            sess.commit()
            inv.sendSeeOther(
                '/reports/301/output/?channel_id=' + str(channel_id))
except utils.UserException as e:
    templater.render(inv, template, make_fields(hh, e), 400)
finally:
    if sess is not None:
        sess.close()
