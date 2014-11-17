from net.sf.chellow.monad import Monad
import datetime
import pytz

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
Channel = db.Channel
UserException, form_int = utils.UserException, utils.form_int

def make_fields(channel, message=None):
    messages = [] if message is None else [str(message)]
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    return {'channel': channel, 'now': now, 'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        channel_id = form_int(inv, 'channel_id')
        channel = Channel.get_by_id(sess, channel_id)
        render(inv, template, make_fields(channel))
    else:
        db.set_read_write(sess)
        channel_id = form_int(inv, 'channel_id')
        channel = Channel.get_by_id(sess, channel_id)
        if inv.hasParameter('delete'):
            supply_id = channel.era.supply.id
            channel.era.delete_channel(
                sess, channel.imp_related, channel.channel_type)
            sess.commit()
            inv.sendSeeOther('/reports/7/output/?supply_id=' + str(supply_id))
        elif inv.hasParameter('delete_data'):
            start_date = form_date(inv, 'start')
            finish_date = form_date(inv, 'finish')
            channel.delete_data(sess, start_date, finish_date)
            sess.commit()
            render(
                inv, template,
                make_fields(channel, "Data successfully deleted."))
        elif inv.hasParameter('insert'):
            start_date = form_date(inv, 'start')
            value = form_decimal(inv, 'value')
            status = form_string(inv, 'status')
            if start_date < channel.era.start_date:
                raise UserException(
                    "The start date is before the start of this era.")
            if hh_after(start_date, channel.era.finish_date):
                raise UserException(
                    "The finish date is after the end of this era.")
            hh_datum = sess.query(HhDatum).filter(
                HhDatum.channel_id == channel.id,
                HhDatum.start_date == start_date).first()
            if hh_datum is not None:
                raise UserException(
                    "There's already a datum in this channel at this time.")
            mpan_core = channel.era.imp_mpan_core
            if mpan_core is None:
                mpan_core = channel.era.exp_mpan_core
            HhDatum.insert(
                sess, [
                    {
                        'start_date': start_date, 'value': value,
                        'status': status, 'mpan_core': mpan_core,
                        'channel_type': channel.channel_type}])
            sess.commit()
            now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
            inv.sendSeeOther(
                '/reports/301/output/?channel_id=' + str(channel_id) +
                "&start_year=" + str(now.year) + "&start_month=" +
                str(now.month))
except UserException, e:
    render(inv, template, make_fields(channel, e))
finally:
    if sess is not None:
        sess.close()
