from net.sf.chellow.monad import Monad
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Channel = db.Channel
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, era, message=None):
    channels = sess.query(Channel).filter(
        Channel.era == era).order_by(Channel.imp_related, Channel.channel_type)
    return {
        'era': era, 'channels': channels,
        'messages': None if message is None else [str(message)]}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        era_id = inv.getLong('era_id')
        era = db.Era.get_by_id(sess, era_id)
        templater.render(inv, template, make_fields(sess, era))
    else:
        db.set_read_write(sess)
        era_id = inv.getLong('era_id')
        imp_related = inv.getBoolean('imp_related')
        channel_type = inv.getString('channel_type')

        era = db.Era.get_by_id(sess, era_id)
        channel = era.insert_channel(sess, imp_related, channel_type)
        sess.commit()
        inv.sendSeeOther('/reports/301/output/?channel_id=' + str(channel.id))
except utils.UserException, e:
    templater.render(inv, template, make_fields(sess, era, e))
finally:
    if sess is not None:
        sess.close()
