from net.sf.chellow.monad import Monad
import datetime
import pytz
from dateutil.relativedelta import relativedelta
import templater
import utils
import db
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
UserException, HH, hh_after = utils.UserException, utils.HH, utils.hh_after
HhDatum, Snag = db.HhDatum, db.Snag
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, channel, start_date, message=None):
    messages = [] if message is None else [str(message)]
    fields = {
        'messages': messages, 'channel': channel, 'start_date': start_date}
    if start_date is not None:
        finish_date = start_date + relativedelta(months=1) - HH
        era = channel.era
        if hh_after(finish_date, era.finish_date):
            messages.append("The finish date is after the end of the era.")
        if start_date < era.start_date:
            messages.append("The start date is before the start of the era.")
        hh_data = sess.query(HhDatum).filter(
            HhDatum.channel_id == channel.id, HhDatum.start_date >= start_date,
            HhDatum.start_date <= finish_date).order_by(HhDatum.start_date)
        snags = sess.query(Snag).filter(
            Snag.channel_id == channel.id).order_by(Snag.start_date)
        fields.update({'hh_data': hh_data, 'snags': snags})
    return fields

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        channel_id = inv.getLong('channel_id')
        channel = db.Channel.get_by_id(sess, channel_id)
        if inv.hasParameter('start_year'):
            start_year = inv.getInteger('start_year')
            start_month = inv.getInteger('start_month')
            try:
                start_date = datetime.datetime(
                    start_year, start_month, 1, tzinfo=pytz.utc)
            except ValueError, e:
                start_date = None
                raise UserException("Invalid date: " + str(e))
        else:
            era_finish = channel.era.finish_date
            if era_finish is None:
                start_date = datetime.datetime.utcnow().replace(
                    tzinfo=pytz.utc)
            else:
                start_date = datetime.datetime(
                    era_finish.year, era_finish.month, 1, tzinfo=pytz.utc)

        render(inv, template, make_fields(sess, channel, start_date))
except UserException, e:
    render(inv, template, make_fields(sess, channel, start_date, e), 400)
finally:
    if sess is not None:
        sess.close()
