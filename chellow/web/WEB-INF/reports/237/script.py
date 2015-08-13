'''
from net.sf.chellow.monad import Hiber, UserException
from java.lang import System
from net.sf.chellow.monad.types import MonadDate
from java.sql import Timestamp, ResultSet
from java.util import GregorianCalendar, Calendar, TimeZone, Locale, Date
from net.sf.chellow.physical import HhStartDate
from java.util.zip import ZipOutputStream, ZipEntry
from java.io import OutputStreamWriter, PrintWriter
from java.text import SimpleDateFormat
import collections

year = inv.getInteger("year")
month = inv.getInteger("month")
months = inv.getInteger("months")

cal = GregorianCalendar(TimeZone.getTimeZone("GMT"), Locale.UK)
cal.set(Calendar.YEAR, year)
cal.set(Calendar.MONTH, month - 1)
cal.set(Calendar.DAY_OF_MONTH, 1)
cal.set(Calendar.HOUR_OF_DAY, 0)
cal.set(Calendar.MINUTE, 0)
cal.set(Calendar.SECOND, 0)
cal.set(Calendar.MILLISECOND, 0)
cal.add(Calendar.MONTH, 1)
cal.add(Calendar.MINUTE, -30)
finish_date = HhStartDate(cal.getTime())

cal.add(Calendar.MINUTE, 30)
cal.add(Calendar.MONTH, -1 * months)
start_date = HhStartDate(cal.getTime())

file_format = SimpleDateFormat("yyyy-MM-dd")
file_format.setCalendar(cal)

inv.getResponse().setContentType("text/csv")
inv.getResponse().setHeader(
    'Content-Disposition',
    'filename="overall-profile_' + file_format.format(Date()) + '.csv"')
pw = inv.getResponse().getWriter()

date_format = SimpleDateFormat("yyyy,MM,dd,HH,mm,dd/MM/yyy HH:mm,")
date_format.setCalendar(cal)

con = Hiber.session().connection()

hh_date = start_date.getDate().getTime()
finish_date_millis = finish_date.getDate().getTime()
stmt = con.prepareStatement("""select hh_datum.value, channel.is_import,
source.code as source_code, pc.code as pc_code from hh_datum, channel,
supply_era, supply, source, pc where hh_datum.channel_id = channel.id and
channel.supply_era_id = supply_era.id and supply_era.supply_id = supply.id
and supply.source_id = source.id and supply_era.pc_id = pc.id
and channel.is_kwh is true and hh_datum.start_date = ?""",
ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY,
ResultSet.CLOSE_CURSORS_AT_COMMIT)
stmt.setFetchSize(100)

prefixes = ['total', 'hh', 'amr']
suffixes = [
    'export-kwh', 'import-kwh', 'parasitic-kwh', 'generated-kwh',
    '3rd-party-import-kwh', '3rd-party-export-kwh']

title_map = dict(
    [
        (
            prefix, dict(
                [
                    (
                        suffix, prefix + '-' + suffix)
                        for suffix in suffixes])) for prefix in prefixes])

titles = [
    'year', 'month', 'day', 'hour', 'minute', 'date', 'total-used-kwh',
    'total-displaced-kwh'] + [title_map[prefix][suffix]
    for prefix in prefixes for suffix in suffixes]

pw.println(','.join(titles))
pw.flush()

while hh_date <= finish_date_millis:
    values = collections.defaultdict(int)
    stmt.setTimestamp(1, Timestamp(hh_date))
    rs = stmt.executeQuery()
    while rs.next():
        hh_val = rs.getFloat("value")
        is_import = rs.getBoolean("is_import")
        source_code = rs.getString("source_code")
        pc_code = rs.getInt("pc_code")
        if pc_code == 0:
            prefix = 'hh'
        else:
            prefix = 'amr'
        type_map = title_map[prefix]
        if not is_import and source_code in ('net', 'gen-net'):
            values[type_map['export-kwh']] += hh_val
        if is_import and source_code in ('net', 'gen-net'):
            values[type_map['import-kwh']] += hh_val
        if (is_import and source_code == 'gen') or \
                (not is_import and source_code == 'gen-net'):
            values[type_map['generated-kwh']] += hh_val
        if (not is_import and source_code == 'gen') or \
                (is_import and source_code == 'gen-net'):
            values[type_map['parasitic-kwh']] += hh_val
        if (is_import and source_code == '3rd-party') or \
                (not is_import and source_code == '3rd-party-reverse'):
            values[type_map['3rd-party-import-kwh']] += hh_val
        if (not is_import and source_code == '3rd-party') or \
                (is_import and source_code == '3rd-party-reverse'):
            values[type_map['3rd-party-export-kwh']] += hh_val

    for suffix in suffixes:
        values[title_map['total'][suffix]] = \
            values[title_map['amr'][suffix]] + \
            values[title_map['hh'][suffix]]
    values['total-displaced-kwh'] = values['total-generated-kwh'] - \
        values['total-export-kwh'] - values['total-parasitic-kwh']
    values['total-used-kwh'] = values['total-displaced-kwh'] + \
        values['total-import-kwh'] + values['total-3rd-party-import-kwh'] - \
        values['total-3rd-party-export-kwh']
    pw.println(
        date_format.format(Date(hh_date)) +
        ','.join(str(values[title]) for title in titles[6:]))
    pw.flush()
    hh_date = HhStartDate.getNext(cal, hh_date)
pw.close()
'''
