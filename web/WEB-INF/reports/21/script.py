from net.sf.chellow.monad import Monad
from sqlalchemy import not_
import datetime
from dateutil.relativedelta import relativedelta
import pytz
import math
import sys
import utils
import db
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
HH = utils.HH
inv = globals()['inv']

if sys.platform.startswith('java'):
    from java.awt.image import BufferedImage
    from javax.imageio import ImageIO
    from java.awt import Font, Color
    sess = None
    try:
        sess = db.session()
        inv.getResponse().setContentType("image/png")

        site_id = inv.getLong("site_id")
        finish_date_year = inv.getInteger("finish_year")
        finish_date_month = inv.getInteger("finish_month")
        months = inv.getInteger("months")

        finish_date = datetime.datetime(
            finish_date_year, finish_date_month, 1,
            tzinfo=pytz.utc) + relativedelta(months=1) - HH
        start_date = datetime.datetime(
            finish_date_year, finish_date_month, 1,
            tzinfo=pytz.utc) - relativedelta(months=months-1)
        site = db.Site.get_by_id(sess, site_id)

        supplies = sess.query(db.Supply).join(db.Source).join(db.Era).join(
            db.SiteEra).distinct().filter(
            db.SiteEra.site_id == site.id,
            not_(db.Source.code.in_(('sub', 'gen-net')))).all()

        res = iter(
            sess.execute(
                "select cast(hh_datum.value as double precision) as value, "
                "hh_datum.start_date as start_date, "
                "hh_datum.status as status, "
                "channel.imp_related as imp_related, "
                "source.code as source_code "
                "from hh_datum, channel, era, supply, source "
                "where hh_datum.channel_id = channel.id "
                "and channel.era_id = era.id "
                "and era.supply_id = supply.id "
                "and supply.source_id = source.id "
                "and channel.channel_type = 'ACTIVE' "
                "and hh_datum.start_date >= :start_date "
                "and hh_datum.start_date <= :finish_date "
                "and supply.id = any(:supply_ids) "
                "order by hh_datum.start_date",
                params={
                    'start_date': start_date, 'finish_date': finish_date,
                    'supply_ids': [s.id for s in supplies]}))

        hh_date = start_date
        max_scale = 2
        min_scale = 0
        result_data = []

        try:
            row = res.next()

            while hh_date <= finish_date:
                complete = "blank"
                hh_value = 0
                while row is not None and row.start_date == hh_date:
                    if (
                            row.imp_related and
                            row.source_code != '3rd-party-reverse') or \
                            (
                                not row.imp_related and
                                row.source_code == '3rd-party-reverse'):
                        hh_value += row.value
                    else:
                        hh_value -= row.value
                    if row.status == 'A':
                        if complete == "blank":
                            complete = "actual"
                    else:
                        complete = "not-actual"
                    try:
                        row = res.next()
                    except StopIteration:
                        row = None

                hh_date += HH
                result_data.append([hh_value, hh_date, complete == "actual"])
                max_scale = max(max_scale, int(math.ceil(hh_value)))
                min_scale = min(min_scale, int(math.floor(hh_value)))

            step = 10**int(math.floor(math.log10(max_scale - min_scale)))
            #raise Exception('step is ' + str(step))

            '''
            if step > (max_scale - minScale) / 2:
                step = int(float(step) / 4)
            '''
        except StopIteration:
            pass

        if len(result_data) > 0:
            graph_left = 100
            image = BufferedImage(
                graph_left + len(result_data) + 100, 400,
                BufferedImage.TYPE_4BYTE_ABGR)
            graphics = image.createGraphics()
            defaultFont = graphics.getFont()
            small_font = Font(
                defaultFont.getName(), defaultFont.getStyle(), 10)
            max_height = 300
            scale_factor = float(max_height) / (max_scale - min_scale)
            graph_top = 50
            x_axis = int(graph_top + max_scale * scale_factor)
            month_points = []
            for i, (value, date, is_complete) in enumerate(result_data):
                hour = date.hour
                minute = date.minute
                height = int(value * scale_factor)
                if is_complete:
                    graphics.setColor(Color.BLUE)
                else:
                    graphics.setColor(Color.GRAY)
                    graphics.fillRect(graph_left + i, graph_top, 1, max_height)
                    graphics.setColor(Color.BLACK)
                if height > 0:
                    graphics.fillRect(
                        graph_left + i, x_axis - height, 1, height)
                else:
                    graphics.fillRect(graph_left + i, x_axis, 1, abs(height))
                if hour == 0 and minute == 0:
                    day = date.day
                    if date.weekday() > 4:
                        graphics.setColor(Color.RED)
                    else:
                        graphics.setColor(Color.BLACK)
                    graphics.drawString(
                        str(day), graph_left + i + 16,
                        graph_top + max_height + 20)
                    graphics.setColor(Color.BLACK)
                    graphics.fillRect(
                        graph_left + i, graph_top + max_height, 1, 5)
                    if day == 15:
                        graphics.drawString(
                            date.strftime("%B"), graph_left + i + 16,
                            graph_top + max_height + 45)
                        month_points.append(i)
            graphics.setColor(Color.BLACK)
            graphics.fillRect(graph_left, graph_top, 1, max_height)

            graphics.setColor(Color.BLACK)

            for point in range(0, max_scale, step) + \
                    range(0, min_scale, step * -1):
                graphics.fillRect(
                    graph_left - 5, int(x_axis - point * scale_factor),
                    len(result_data) + 5, 1)
                graphics.drawString(
                    str(point * 2), graph_left - 40,
                    int(x_axis - point * scale_factor + 5))
                for month_point in month_points:
                    graphics.drawString(
                        str(point * 2), graph_left + month_point + 16,
                        int(x_axis - point * scale_factor - 2))

            graphics.drawString("kW", graph_left - 90, 100)
            title = "Electricity use at site " + site.code + " " + \
                site.name + " for " + str(months) + " month"
            if months > 1:
                title += "s"
            title += " ending " + finish_date.strftime("%B %Y")
            graphics.drawString(title, 30, 30)
            graphics.setFont(small_font)
            graphics.drawString(
                "Poor data is denoted by a grey background and black "
                "foreground.", 30, 395)
        else:
            image = BufferedImage(400, 400, BufferedImage.TYPE_4BYTE_ABGR)
            graphics = image.createGraphics()
            graphics.setColor(Color.BLACK)
            graphics.drawString("No data available for this period.", 30, 10)

        os = inv.getResponse().getOutputStream()
        graphics.setColor(Color.BLACK)

        ImageIO.write(image, "png", os)
        os.close()
    finally:
        if sess is not None:
            sess.close()
else:
    from flask import Response

    inv.response = Response("Stub", status=200)
