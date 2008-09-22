from net.sf.chellow.monad import Hiber, UserException
from net.sf.chellow.physical import HhEndDate, HhDatum
from net.sf.chellow.monad.types import MonadDate
from java.awt.image import BufferedImage
from javax.imageio import ImageIO
from java.awt import Color, Font
import math
from java.sql import Timestamp, ResultSet
from java.text import DateFormat
from java.lang import System
from java.util import GregorianCalendar, TimeZone, Locale, Calendar, Date

colour_list = [Color.BLUE, Color.GREEN, Color.RED, Color.YELLOW, Color.MAGENTA, Color.CYAN, Color.PINK]

def set_colour(graphics, supplies, id, name, source_code):
    if not id in supplies:
        supplies[id] = [len(supplies), name, source_code]
    graphics.setColor(colour_list[supplies[id][0]])

def paint_legend(supplies, graph_top):
    i = 0
    for supply in supplies.values():
        graphics.setColor(colour_list[supply[0]])
        graphics.fillRect(12, int(graph_top + 15 + (10 * i)), 8, 8)
        graphics.setColor(Color.BLACK)
        graphics.drawString(supply[2] + ' ' + supply[1], 25, int(graph_top + 22 + (10 * i)))
        i = i + 1        

def minimum_scale(min_scale, max_scale):
    if min_scale == 0 and max_scale == 0:
        min_scale = 0
        max_scale = 10
    if min_scale < 0 and min_scale > -10:
        min_scale = -10
    if max_scale > 0 and max_scale < 10:
        max_scale = 10
    return min_scale, max_scale

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
stmt = con.prepareStatement("select hh_datum.value, hh_datum.end_date, hh_datum.status, channel.is_import, supply.name, source.code, supply.id from hh_datum, channel, supply_generation, supply, source where hh_datum.channel_id = channel.id and channel.supply_generation_id = supply_generation.id and supply_generation.supply_id = supply.id and supply.source_id = source.id and channel.is_kwh is true and hh_datum.end_date >= ? and hh_datum.end_date <= ? and supply.id in (" + suppliesSQL[:-1] + ") order by hh_datum.end_date, supply.id", ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY, ResultSet.CLOSE_CURSORS_AT_COMMIT)
stmt.setTimestamp(1, Timestamp(startDate.getTime()))
stmt.setTimestamp(2, Timestamp(finishDate.getTime()))
stmt.setFetchSize(100)
rs = stmt.executeQuery()
hhDate = HhEndDate(startDate).getDate().getTime()
maxHeight = 80
pxStep = 10
maxOverallScale = 0
minOverallScale = 0
maxExportedScale = 0
minExportedScale = 0
maxImportedScale = 0
minImportedScale = 0
maxGeneratedScale = 0
maxParasiticScale = 0
maxDisplacedScale = 0
minDisplacedScale = 0
maxUsedScale = 0
minUsedScale = 0
resultData = []
actualStatus = HhDatum.ACTUAL
if rs.next():
    hhChannelValue = rs.getFloat("value")
    hhChannelEndDate = rs.getTimestamp("end_date")
    isImport = rs.getBoolean("is_import")
    status = rs.getString("status")
    sourceCode = rs.getString("code")
    supplyName = rs.getString("name")
    supply_id = rs.getLong('id')
    finishDateMillis = finishDate.getTime()
    cal = MonadDate.getCalendar()
    while hhDate <= finishDateMillis:
        complete = "blank"
        exportedValue = 0
        importedValue = 0
        parasiticValue = 0
        generatedValue = 0
        supplyList = []
        while hhChannelEndDate != None and hhChannelEndDate.getTime() == hhDate:
            if not isImport and sourceCode == "net":
                exportedValue = exportedValue + hhChannelValue
            if isImport and sourceCode == "net":
                importedValue = importedValue + hhChannelValue
            if isImport and (sourceCode == "lm" or sourceCode == "chp" or sourceCode == "turb"):
                generatedValue = generatedValue + hhChannelValue
            if not isImport and (sourceCode == "lm" or sourceCode == "chp" or sourceCode == "turb"):
                parasiticValue = parasiticValue + hhChannelValue
            supplyList.append([supplyName, sourceCode, isImport, hhChannelValue, supply_id])
            if rs.next():
                sourceCode = rs.getString("code")
                supplyName = rs.getString("name")
                hhChannelValue = rs.getFloat("value")
                hhChannelEndDate = rs.getTimestamp("end_date")
                isImport = rs.getBoolean("is_import")
                status = rs.getString("status")
                supply_id = rs.getLong('id')
            else:
                hhChannelEndDate = None
        maxExportedScale = max(maxExportedScale, exportedValue)
        minExportedScale = min(minExportedScale, exportedValue)
        maxImportedScale = max(maxImportedScale, importedValue)
        minImportedScale = min(minImportedScale, importedValue)
        maxGeneratedScale = max(maxGeneratedScale, generatedValue)
        maxParasiticScale = max(maxParasiticScale, parasiticValue)
        displacedValue = generatedValue - parasiticValue - exportedValue
        maxDisplacedScale = max(maxDisplacedScale, displacedValue)
        minDisplacedScale = min(minDisplacedScale, displacedValue)
        usedValue = importedValue + displacedValue
        maxUsedScale = max(maxUsedScale, usedValue)
        minUsedScale = min(minUsedScale, usedValue)
        resultData.append([hhDate, supplyList, usedValue, displacedValue])
        hhDate = HhEndDate.getNext(cal, hhDate)
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter("ResultData: " + str(resultData)) 
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter("Overall: " + str(maxOverallScale) + " " + str(minOverallScale) + " Exported: " + str(maxExportedScale) + " " + str(minExportedScale) + " Imported: " + str(maxImportedScale) + " " + str(minImportedScale) + " Generated: " + str(maxGeneratedScale) + " Parasitic: " + str(maxParasiticScale) + " Displaced: " + str(maxDisplacedScale) + " " + str(minDisplacedScale) + " Used: " + str(maxUsedScale) + " " + str(minUsedScale))
    minimized_scale = minimum_scale(minExportedScale, maxExportedScale)
    minExportedScale = minimized_scale[0]
    maxExportedScale = minimized_scale[1]
    minimized_scale = minimum_scale(minImportedScale, maxImportedScale)
    minImportedScale = minimized_scale[0]
    maxImportedScale = minimized_scale[1]
    if maxGeneratedScale == 0 and maxParasiticScale == 0:
        maxGeneratedScale = 10
        maxParasiticScale = 10
    minimized_scale = minimum_scale(minUsedScale, maxUsedScale)
    minUsedScale = minimized_scale[0]
    maxUsedScale = minimized_scale[1]
    minimized_scale = minimum_scale(minDisplacedScale, maxDisplacedScale)
    minDisplacedScale = minimized_scale[0]
    maxDisplacedScale = minimized_scale[1]
    maxOverallScale = max(maxExportedScale, maxImportedScale, maxGeneratedScale, maxDisplacedScale, maxUsedScale)
    minOverallScale = min(minExportedScale, minImportedScale, minDisplacedScale, minUsedScale)
    rawStepOverall = (maxOverallScale * 2) / (maxHeight / pxStep)
    factorOverall = 10**int(math.floor(math.log10(rawStepOverall)))
    endOverall = rawStepOverall / factorOverall
    newEndOverall = 1
    if endOverall >= 2:
        newEndOverall = 2
    if endOverall >= 5:
        newEndOverall = 5
    stepOverall = newEndOverall * factorOverall
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter("Overall Step: " + str(stepOverall))
if len(resultData) > 0:
    graphLeft = 180
    scaleFactorOverall = float(maxHeight) / maxOverallScale
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter(str(scaleFactorExported) + " " + str(scaleFactorUsed) + " " + str(scaleFactorDisplaced) + " " + str(scaleFactorImported) + " " + str(scaleFactorGenerated))
    graphOrderExported = 5
    graphOrderImported = 4
    graphOrderGenerated = 3
    graphOrderUsed = 1
    graphOrderDisplaced = 2
    minUsed = 0
    minDisplaced = 0
    minParasitic = 0
    for i in range(0, int(minUsedScale), stepOverall * -1):
        minUsed = min(minUsed, i)
    for i in range(0, int(minDisplacedScale), stepOverall * -1):
        minDisplaced = min(minDisplaced, i)
    for i in range(0, int(maxParasiticScale), stepOverall):
        minParasitic = max(minParasitic, i)
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter(str(int((abs(minParasitic)) * scaleFactorOverall)))
    minUsed = int(abs(minUsed) * scaleFactorOverall)
    minDisplaced = int(abs(minDisplaced) * scaleFactorOverall)
    minParasitic = int(abs(minParasitic) * scaleFactorOverall)
    graphTopExported = ((graphOrderExported - 1) * (maxHeight + 22)) + 30 + minUsed + minDisplaced + minParasitic
    graphTopImported = ((graphOrderImported - 1) * (maxHeight + 22)) + 30 + minUsed + minDisplaced + minParasitic
    graphTopGenerated = ((graphOrderGenerated - 1) * (maxHeight + 22)) + 30 + minUsed + minDisplaced
    graphTopUsed = ((graphOrderUsed - 1) * (maxHeight + 22)) + 30
    graphTopDisplaced = ((graphOrderDisplaced - 1) * (maxHeight + 22)) + 30 + minUsed
    image = BufferedImage(graphLeft + len(resultData) + 100, ((maxHeight + 22) * 5) + 60 + minUsed + minDisplaced + minParasitic, BufferedImage.TYPE_4BYTE_ABGR)
    graphics = image.createGraphics()
    defaultFont = graphics.getFont()
    smallFont = Font(defaultFont.getName(), defaultFont.getStyle(), 10)
    keyFont = Font(defaultFont.getName(), defaultFont.getStyle(), 9)
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter(str(graphTopExported) + " " + str(graphTopImported) + " " + str(graphTopUsed) + " " + str(graphTopDisplaced))
    xAxisExported = int(graphTopExported + maxOverallScale * scaleFactorOverall)
    xAxisImported = int(graphTopImported + maxOverallScale * scaleFactorOverall)
    xAxisGenerated = int(graphTopGenerated + maxOverallScale * scaleFactorOverall)
    xAxisUsed = int(graphTopUsed + maxOverallScale * scaleFactorOverall)
    xAxisDisplaced = int(graphTopDisplaced + maxOverallScale * scaleFactorOverall)
    monthDateFormat = DateFormat.getDateInstance(DateFormat.LONG, Locale.UK)
    monthDateFormat.applyLocalizedPattern("MMMMMM")
    yearDateFormat = DateFormat.getDateInstance(DateFormat.LONG, Locale.UK)
    yearDateFormat.applyLocalizedPattern("yyyy")
    generated_supplies = {}
    imported_supplies = {}
    exported_supplies = {}
    monthPoints = []
    for i in range(len(resultData)):
        dataHh = resultData[i]
        date = dataHh[0]
        usedValue = dataHh[2]
        displacedValue = dataHh[3]
        dataHhSupplyList = dataHh[1]
        cal.setTimeInMillis(date)
        hour = cal.get(Calendar.HOUR_OF_DAY)
        minute = cal.get(Calendar.MINUTE)
        graphics.setColor(Color.BLUE)
        usedHeight = int(usedValue * scaleFactorOverall)
        if usedHeight < 0:
            graphics.fillRect(graphLeft + i, xAxisUsed, 1, abs(usedHeight))
        else:
            graphics.fillRect(graphLeft + i, xAxisUsed - usedHeight, 1, usedHeight)
        displacedHeight = int(displacedValue * scaleFactorOverall)
        if displacedHeight < 0:
            graphics.fillRect(graphLeft + i, xAxisDisplaced, 1, abs(displacedHeight))
        else:
            graphics.fillRect(graphLeft + i, xAxisDisplaced - displacedHeight, 1, displacedHeight)
        generatedTotal = 0
        parasiticTotal = 0
        importedTotal = 0
        exportedTotal = 0
        for j in dataHhSupplyList:
            name = j[0]
            source = j[1]
            isImport = j[2]
            value = j[3]
            id = j[4]
            height = int(value * scaleFactorOverall)
            if  source == "net" and not isImport:
                set_colour(graphics, exported_supplies, id, name, source)
                exportedTotal = exportedTotal + height
                graphics.fillRect(graphLeft + i, xAxisExported - exportedTotal, 1, height)
            if  source == "net" and isImport:
                set_colour(graphics, imported_supplies, id, name, source)
                importedTotal = importedTotal + height
                graphics.fillRect(graphLeft + i, xAxisImported - importedTotal, 1, height)
            if isImport and (source == "lm"):
                set_colour(graphics, generated_supplies, id, name, source)
                generatedTotal = generatedTotal + height
                graphics.fillRect(graphLeft + i, xAxisGenerated - generatedTotal, 1, height)
            if isImport and (source == "chp"):
                set_colour(graphics, generated_supplies, id, name, source)
                generatedTotal = generatedTotal + height
                graphics.fillRect(graphLeft + i, xAxisGenerated -  generatedTotal, 1, height)
            if isImport and (source == "turb"):
                set_colour(graphics, generated_supplies, id, name, source)
                generatedTotal = generatedTotal + height
                graphics.fillRect(graphLeft + i, xAxisGenerated - generatedTotal, 1, height)
            if not isImport and (source == "lm"):
                set_colour(graphics, generated_supplies, id, name, source)
                parasiticTotal = parasiticTotal + height
                graphics.fillRect(graphLeft + i, xAxisGenerated, 1, height)
            if not isImport and (source == "chp"):
                set_colour(graphics, generated_supplies, id, name, source)
                parasiticTotal = parasiticTotal + height
                graphics.fillRect(graphLeft + i, xAxisGenerated, 1, height)
            if not isImport and (source == "turb"):
                set_colour(graphics, generated_supplies, id, name, source)
                parasiticTotal = parasiticTotal + height
                graphics.fillRect(graphLeft + i, xAxisGenerated, 1, height) 
        if hour == 0 and minute == 30:
            day = cal.get(Calendar.DAY_OF_MONTH)
            dayOfWeek = cal.get(Calendar.DAY_OF_WEEK)
            if dayOfWeek == 7 or dayOfWeek == 1:
                graphics.setColor(Color.RED)
            else:
                graphics.setColor(Color.BLACK)
            graphics.drawString(str(day), graphLeft + i + 16, ((maxHeight + 22) * 5) + 30 + minUsed + minDisplaced + minParasitic)
            graphics.setColor(Color.BLACK)
            graphics.fillRect(graphLeft + i, graphTopExported + maxHeight, 1, 5)
            graphics.fillRect(graphLeft + i, graphTopImported + maxHeight, 1, 5)
            graphics.fillRect(graphLeft + i, graphTopGenerated + maxHeight, 1, 5)
            graphics.fillRect(graphLeft + i, graphTopUsed + maxHeight, 1, 5)
            graphics.fillRect(graphLeft + i, graphTopDisplaced + maxHeight, 1, 5)
            if day == 15:
                graphics.drawString(monthDateFormat.format(cal.getTime()), graphLeft + i + 16, ((maxHeight + 22) * 5) + 50 + minUsed + minDisplaced + minParasitic)
                monthPoints.append(i)
    graphics.setColor(Color.BLACK)
    graphics.fillRect(graphLeft, graphTopExported, 1, maxHeight)
    graphics.fillRect(graphLeft, graphTopImported, 1, maxHeight)
    graphics.fillRect(graphLeft, graphTopGenerated, 1, maxHeight + minParasitic)
    graphics.fillRect(graphLeft, graphTopUsed, 1, maxHeight + minUsed)
    graphics.fillRect(graphLeft, graphTopDisplaced, 1, maxHeight + minDisplaced)
    scalePointsExported = []
    for i in range(0, int(maxOverallScale), stepOverall):
        scalePointsExported.append(i)
    #for i in range(0, int(minExportedScale), stepOverall * -1):
        #scalePointsExported.append(i)
    graphics.setColor(Color.BLACK)
    for point in scalePointsExported:
        graphics.fillRect(graphLeft - 5, int(xAxisExported - point * scaleFactorOverall), len(resultData) + 5, 1)
        graphics.drawString(str(point * 2), graphLeft - 40, int(xAxisExported - point * scaleFactorOverall + 5))
        for monthPoint in monthPoints:
            graphics.drawString(str(point * 2), graphLeft + monthPoint + 16, int(xAxisExported - point * scaleFactorOverall - 2))
    scalePointsImported = []
    for i in range(0, int(maxOverallScale), stepOverall):
        scalePointsImported.append(i)
    #for i in range(0, int(minOverallScale), stepOverall * -1):
        #scalePointsImported.append(i)
    graphics.setColor(Color.BLACK)
    for point in scalePointsImported:
        graphics.fillRect(graphLeft - 5, int(xAxisImported - point * scaleFactorOverall), len(resultData) + 5, 1)
        graphics.drawString(str(point * 2), graphLeft - 40, int(xAxisImported - point * scaleFactorOverall + 5))
        for monthPoint in monthPoints:
            graphics.drawString(str(point * 2), graphLeft + monthPoint + 16, int(xAxisImported - point * scaleFactorOverall - 2))
    scalePointsGenerated = []
    for i in range(0, int(maxOverallScale), stepOverall):
        scalePointsGenerated.append(i)
    for i in range(0, int(maxParasiticScale), stepOverall):
        scalePointsGenerated.append(i * -1)
    graphics.setColor(Color.BLACK)
    for point in scalePointsGenerated:
        graphics.fillRect(graphLeft - 5, int(xAxisGenerated - point * scaleFactorOverall), len(resultData) + 5, 1)
        graphics.drawString(str(point * 2), graphLeft - 40, int(xAxisGenerated - point * scaleFactorOverall + 5))
        for monthPoint in monthPoints:
            graphics.drawString(str(point * 2), graphLeft + monthPoint + 16, int(xAxisGenerated - point * scaleFactorOverall - 2))
    scalePointsUsed = []
    for i in range(0, int(maxOverallScale), stepOverall):
        scalePointsUsed.append(i)
    for i in range(0, int(minUsedScale), stepOverall * -1):
        scalePointsUsed.append(i)
    for point in scalePointsUsed:
        graphics.fillRect(graphLeft - 5, int(xAxisUsed - point * scaleFactorOverall), len(resultData) + 5, 1)
        graphics.drawString(str(point * 2), graphLeft - 40, int(xAxisUsed - point * scaleFactorOverall + 5))
        for monthPoint in monthPoints:
            graphics.drawString(str(point * 2), graphLeft + monthPoint + 16, int(xAxisUsed - point * scaleFactorOverall - 2))
    scalePointsDisplaced = []
    for i in range(0, int(maxOverallScale), stepOverall):
        scalePointsDisplaced.append(i)
    for i in range(0, int(minDisplacedScale), stepOverall * -1):
        scalePointsDisplaced.append(i)
    for point in scalePointsDisplaced:
        graphics.fillRect(graphLeft - 5, int(xAxisDisplaced - point * scaleFactorOverall), len(resultData) + 5, 1)
        graphics.drawString(str(point * 2), graphLeft - 40, int(xAxisDisplaced - point * scaleFactorOverall + 5))
        for monthPoint in monthPoints:
            graphics.drawString(str(point * 2), graphLeft + monthPoint + 16, int(xAxisDisplaced - point * scaleFactorOverall - 2))
    graphics.drawString("kW", graphLeft - 90, graphTopExported + 10)
    graphics.drawString("kW", graphLeft - 90, graphTopImported + 10)
    graphics.drawString("kW", graphLeft - 90, graphTopGenerated + 10)
    graphics.drawString("kW", graphLeft - 90, graphTopUsed + 10)
    graphics.drawString("kW", graphLeft - 90, graphTopDisplaced + 10)
    title = "Electricity generation at site " + site.getCode().toString() + " " + site.getName() + " for " + str(months) + " month"
    if months > 1:
        title = title + "s"
    title = title + " ending " + monthDateFormat.format(Date(finishDate.getTime() - 1)) + " " + yearDateFormat.format(Date(finishDate.getTime() - 1))
    graphics.drawString(title, 30, 20)
    graphics.drawString("Imported", 10, graphTopImported + 10)
    graphics.drawString("Exported", 10, graphTopExported + 10)
    graphics.drawString("Generated", 10, graphTopGenerated + 10)
    graphics.drawString("Used", 10, graphTopUsed + 10)
    graphics.drawString("Displaced", 10, graphTopDisplaced + 10)
    graphics.setFont(smallFont)
    graphics.drawString("Poor data is denoted by a grey background and black foreground.", 30, ((maxHeight + 22) * 5) + 50 + minUsed + minDisplaced + minParasitic)
    graphics.setFont(keyFont)
    paint_legend(exported_supplies, graphTopExported)
    paint_legend(imported_supplies, graphTopImported)
    paint_legend(generated_supplies, graphTopGenerated)
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