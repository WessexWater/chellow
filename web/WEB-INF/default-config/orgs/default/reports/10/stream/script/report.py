from net.sf.chellow.monad import Hiber, UserException
from java.lang import System
from net.sf.chellow.monad.types import MonadDate 
from java.util import GregorianCalendar, TimeZone, Locale, Calendar, Date
from java.awt.image import BufferedImage
from javax.imageio import ImageIO
from java.awt import Font, Color
import math
from java.sql import ResultSet, Timestamp
from java.text import DateFormat
from net.sf.chellow.physical import HhEndDate, HhDatumStatus

start = System.currentTimeMillis()
inv.getResponse().setContentType("image/png")
siteId = inv.getLong("site-id")
finishDateYear = inv.getInteger("finish-date-year")
finishDateMonth = inv.getInteger("finish-date-month")
months = inv.getInteger("months")
if not inv.isValid():
    raise UserException.newInvalidParameter()
cal = GregorianCalendar(TimeZone.getTimeZone("GMT"), Locale.UK)
cal.clear()
cal.set(Calendar.YEAR, finishDateYear)
cal.set(Calendar.MONTH, finishDateMonth)
cal.set(Calendar.DAY_OF_MONTH, 1)
finishDate = cal.getTime()
cal.add(Calendar.MONTH, -1 * months)
startDate = cal.getTime()
cal.setTime(finishDate)
cal.add(Calendar.DAY_OF_MONTH, -1)

site = organization.getSite(siteId)
supplies = Hiber.session().createQuery("select distinct supply from Supply supply join supply.generations supplyGeneration join supplyGeneration.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site = :site and supply.source.code != 'sub'").setEntity('site', site).list()
suppliesSQL = ''
for supply in supplies:
    suppliesSQL = suppliesSQL + str(supply.getId()) + ','
con = Hiber.session().connection()
stmt = con.prepareStatement("select hh_datum.value, hh_datum.end_date, hh_datum.status, channel.is_import from hh_datum, channel, supply_generation, supply where hh_datum.channel_id = channel.id and channel.supply_generation_id = supply_generation.id and supply_generation.supply_id = supply.id and channel.is_kwh is true and hh_datum.end_date >= ? and hh_datum.end_date <= ? and supply.id in (" + suppliesSQL[:-1] + ") order by hh_datum.end_date", ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY, ResultSet.CLOSE_CURSORS_AT_COMMIT)
stmt.setTimestamp(1, Timestamp(startDate.getTime()))
stmt.setTimestamp(2, Timestamp(finishDate.getTime()))
stmt.setFetchSize(100)
rs = stmt.executeQuery()
hhDate = HhEndDate(startDate).getDate().getTime()
maxScale = 0
minScale = 0
resultData = []
actualStatus = HhDatumStatus.ACTUAL
if rs.next():
    hhChannelValue = rs.getFloat("value")
    hhChannelEndDate = rs.getTimestamp("end_date")
    isImport = rs.getBoolean("is_import")
    status = rs.getString("status")
    finishDateMillis = finishDate.getTime()
    cal = MonadDate.getCalendar()
    while hhDate <= finishDateMillis:
        complete = "blank"
        hhValue = 0
        while hhChannelEndDate != None and hhChannelEndDate.getTime() == hhDate:
            if isImport:
                hhValue = hhValue + hhChannelValue
            else:
                hhValue = hhValue - hhChannelValue
            if status == actualStatus:
                if complete == "blank":
                    complete = "actual"
            else:
                complete = "not-actual"
            if rs.next():
                hhChannelValue = rs.getFloat("value")
                hhChannelEndDate = rs.getTimestamp("end_date")
                isImport = rs.getBoolean("is_import")
                status = rs.getString("status")
            else:
                hhChannelEndDate = None
        hhDate = HhEndDate.getNext(cal, hhDate)
        resultData.append([hhValue, hhDate, complete == "actual"])
        maxScale = max(maxScale, hhValue)
        minScale = min(minScale, hhValue)
    System.err.println('ooostep is max scale' + str(maxScale) + ' min scale ' + str(minScale))
    if maxScale > 0 and maxScale < 10:
        maxScale = 10
    if minScale < 0 and minScale > -10:
        minScale = -10
    if minScale == 0 and maxScale == 0:
        minScale = 10
        maxScale = 10
    System.err.println('pppstep is max scale' + str(maxScale) + ' min scale ' + str(minScale))
    step = 10**int(math.floor(math.log10(maxScale - minScale)))
    System.err.println('kkstep is ' + str(step) + ' max scale' + str(maxScale) + ' min scale ' + str(minScale))
    if step > (maxScale - minScale) / 2:
        step = int(float(step) / 4)
if len(resultData) > 0:
    graphLeft = 100
    image = BufferedImage(graphLeft + len(resultData) + 100, 400, BufferedImage.TYPE_4BYTE_ABGR)
    graphics = image.createGraphics()
    defaultFont = graphics.getFont()
    smallFont = Font(defaultFont.getName(), defaultFont.getStyle(), 10)
    maxHeight = 300
    scaleFactor = float(maxHeight) / (maxScale - minScale)
    graphTop = 50
    xAxis = int(graphTop + maxScale * scaleFactor)
    monthDateFormat = DateFormat.getDateInstance(DateFormat.LONG, Locale.UK)
    monthDateFormat.applyLocalizedPattern("MMMMMM")
    yearDateFormat = DateFormat.getDateInstance(DateFormat.LONG, Locale.UK)
    yearDateFormat.applyLocalizedPattern("yyyy")
    monthPoints = []
    for i in range(len(resultData)):
        dataHh = resultData[i]
        value = dataHh[0]
        date = dataHh[1]
        cal.setTimeInMillis(date)
        hour = cal.get(Calendar.HOUR_OF_DAY)
        minute = cal.get(Calendar.MINUTE)
        height = int(value * scaleFactor)
        if dataHh[2]:
            graphics.setColor(Color.BLUE)
        else:
            graphics.setColor(Color.GRAY)
            graphics.fillRect(graphLeft + i, graphTop, 1, maxHeight)
            graphics.setColor(Color.BLACK)
        if height > 0:
            graphics.fillRect(graphLeft + i, xAxis - height, 1, height)
        else:
            graphics.fillRect(graphLeft + i, xAxis, 1, abs(height))
        if hour == 0 and minute == 30:
            day = cal.get(Calendar.DAY_OF_MONTH)
            dayOfWeek = cal.get(Calendar.DAY_OF_WEEK)
            if dayOfWeek == 7 or dayOfWeek == 1:
                graphics.setColor(Color.RED)
            else:
                graphics.setColor(Color.BLACK)
            graphics.drawString(str(day), graphLeft + i + 16, graphTop + maxHeight + 20)
            graphics.setColor(Color.BLACK)
            graphics.fillRect(graphLeft + i, graphTop + maxHeight, 1, 5)
            if day == 15:
                graphics.drawString(monthDateFormat.format(cal.getTime()), graphLeft + i + 16, graphTop + maxHeight + 45)
                monthPoints.append(i)
    graphics.setColor(Color.BLACK)
    graphics.fillRect(graphLeft, graphTop, 1, maxHeight)
    scalePoints = []
    System.err.println('step is ' + str(step) + ' max scale' + str(maxScale) + ' min scale ' + str(maxScale))
    for i in range(0, int(maxScale), step):
        scalePoints.append(i)
    for i in range(0, int(minScale), step * -1):
        scalePoints.append(i)
    graphics.setColor(Color.BLACK)
    for point in scalePoints:
        graphics.fillRect(graphLeft - 5, int(xAxis - point * scaleFactor), len(resultData) + 5, 1)
        graphics.drawString(str(point * 2), graphLeft - 40, int(xAxis - point * scaleFactor + 5))
        for monthPoint in monthPoints:
            graphics.drawString(str(point * 2), graphLeft + monthPoint + 16, int(xAxis - point * scaleFactor - 2))
    graphics.drawString("kW", graphLeft - 90, 100)
    title = "Electricity use at site " + site.getCode().toString() + " " + site.getName() + " for " + str(months) + " month"
    if months > 1:
        title = title + "s"
    title = title + " ending " + monthDateFormat.format(Date(finishDate.getTime() - 1)) + " " + yearDateFormat.format(Date(finishDate.getTime() - 1))
    graphics.drawString(title, 30, 30)
    graphics.setFont(smallFont)
    graphics.drawString("Poor data is denoted by a grey background and black foreground.", 30, 395)
else:
    image = BufferedImage(400, 400, BufferedImage.TYPE_4BYTE_ABGR)
    graphics = image.createGraphics()
    graphics.setColor(Color.BLACK)
    graphics.drawString("No data available for this period.", 30, 10)

os = inv.getResponse().getOutputStream()
graphics.setColor(Color.BLACK)
#graphics.drawString("report took..." + str(java.lang.System.currentTimeMillis() - start) + "ms", 10, 390)
ImageIO.write(image, "png", os)
os.close()