import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import net.sf.chellow.monad.vf.bo
import java.awt.image
import javax.imageio
import java.awt
import math
import java.sql
import java.text

start = java.lang.System.currentTimeMillis()
inv.getResponse().setContentType("image/png")
siteId = inv.getMonadLong("site-id")
finishDateYear = inv.getMonadInteger("finish-date-year")
finishDateMonth = inv.getMonadInteger("finish-date-month")
months = inv.getMonadInteger("months")
#if not inv.isValid():
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter()
months = months.getInteger()
cal = java.util.GregorianCalendar(java.util.TimeZone.getTimeZone("GMT"), java.util.Locale.UK)
cal.clear()
cal.set(java.util.Calendar.YEAR, finishDateYear.getInteger())
cal.set(java.util.Calendar.MONTH, finishDateMonth.getInteger())
cal.set(java.util.Calendar.DAY_OF_MONTH, 1)
finishDate = cal.getTime()
cal.add(java.util.Calendar.MONTH, -1 * months)
startDate = cal.getTime()
cal.setTime(finishDate)
cal.add(java.util.Calendar.DAY_OF_MONTH, -1)

site = organization.getSite(siteId)
con = net.sf.chellow.persistant08.Hiber.session().connection()
stmt = con.prepareStatement("select hh_datum.value, hh_datum.end_date, hh_datum.status, channel.is_import, supply.name, source.code from main.hh_datum hh_datum, main.channel channel, main.supply supply, main.site_supply site_supply, main.site site, main.source source where hh_datum.channel_id = channel.id and channel.supply_id = supply.id and supply.id = site_supply.supply_id and site_supply.site_id = site.id and supply.source_id = source.id and site.code = ? and channel.is_kwh is true and hh_datum.end_date >= ? and hh_datum.end_date <= ? and source.code != 'sub' order by hh_datum.end_date", java.sql.ResultSet.TYPE_FORWARD_ONLY, java.sql.ResultSet.CONCUR_READ_ONLY, java.sql.ResultSet.CLOSE_CURSORS_AT_COMMIT)
stmt.setString(1, site.getCode().toString())
stmt.setTimestamp(2, java.sql.Timestamp(startDate.getTime()))
stmt.setTimestamp(3, java.sql.Timestamp(finishDate.getTime()))
stmt.setFetchSize(100)
rs = stmt.executeQuery()
hhDate = net.sf.chellow.persistant08.HhEndDate(startDate).getDate().getTime()
maxHeight = 300
pxStep = 50
maxExportedScale = 0
minExportedScale = 0
maxImportedScale = 0
minImportedScale = 0
maxGeneratedScale = 0
minGeneratedScale = 0
maxParasiticScale = 0
maxDisplacedScale = 0
minDisplacedScale = 0
maxUsedScale = 0
minUsedScale = 0
resultData = []
actualStatus = net.sf.chellow.persistant08.HhDatumStatus.ACTUAL.getCharacter()
if rs.next():
    hhChannelValue = rs.getFloat("value")
    hhChannelEndDate = rs.getTimestamp("end_date")
    isImport = rs.getBoolean("is_import")
    status = rs.getString("status")
    sourceCode = rs.getString("code")
    supplyName = rs.getString("name")
    finishDateMillis = finishDate.getTime()
    cal = net.sf.chellow.monad.vf.bo.MonadDate.getCalendar()
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
                #if hhChannelValue > 50:
                    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter(str(hhChannelValue) + " " + str(hhDate))
                generatedValue = generatedValue + hhChannelValue
            if not isImport and (sourceCode == "lm" or sourceCode == "chp" or sourceCode == "turb"):
                parasiticValue = parasiticValue + hhChannelValue
            supplyList.append([supplyName, sourceCode, isImport, hhChannelValue])
            if rs.next():
                sourceCode = rs.getString("code")
                supplyName = rs.getString("name")
                hhChannelValue = rs.getFloat("value")
                hhChannelEndDate = rs.getTimestamp("end_date")
                isImport = rs.getBoolean("is_import")
                status = rs.getString("status")
            else:
                hhChannelEndDate = None
        maxExportedScale = max(maxExportedScale, exportedValue)
        minExportedScale = min(minExportedScale, exportedValue)
        maxImportedScale = max(maxImportedScale, importedValue)
        minImportedScale = min(minImportedScale, importedValue)
        maxGeneratedScale = max(maxGeneratedScale, generatedValue)
        minGeneratedScale = min(minGeneratedScale, generatedValue)
        displacedValue = generatedValue - parasiticValue - exportedValue
        maxDisplacedScale = max(maxDisplacedScale, displacedValue)
        minDisplacedScale = min(minDisplacedScale, displacedValue)
        usedValue = importedValue + displacedValue
        maxUsedScale = max(maxUsedScale, usedValue)
        minUsedScale = min(minUsedScale, usedValue)
        resultData.append([hhDate, supplyList, usedValue, displacedValue])
        hhDate = net.sf.chellow.persistant08.HhEndDate.getNext(cal, hhDate)
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter(str(resultData))
    if minExportedScale == 0 and maxExportedScale == 0:
        maxExportedScale = 100
        minExportedScale = 0
    if minImportedScale == 0 and maxImportedScale == 0:
        maxImportedScale = 100
        minImportedScale = 0
    if maxGeneratedScale == 0 and minGeneratedScale == 0:
        maxGeneratedScale = 100
        minGeneratedScale = 0
    if minUsedScale == 0 and maxUsedScale == 0:
        maxUsedScale = 100
        minUsedScale = 0
    if minDisplacedScale == 0 and maxDisplacedScale == 0:
        maxDisplacedScale = 100
        minDisplacedScale = 0
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter(str(maxGeneratedScale) + " " + str(maxParasiticScale))
    rawStepExported = ((maxExportedScale - minExportedScale) * 2) / (maxHeight / pxStep)
    factorExported = 10**int(math.floor(math.log10(rawStepExported)))
    endExported = rawStepExported / factorExported
    newEndExported = 1
    if endExported >= 2:
        newEndExported = 2
    if endExported >= 5:
        newEndExported = 5
    stepExported = newEndExported * factorExported
    rawStepImported = ((maxImportedScale - minImportedScale) * 2) / (maxHeight / pxStep)
    factorImported = 10**int(math.floor(math.log10(rawStepImported)))
    endImported = rawStepImported / factorImported
    newEndImported = 1
    if endImported >= 2:
        newEndImported = 2
    if endImported >= 5:
        newEndImported = 5
    stepImported = newEndImported * factorImported
    rawStepGenerated = ((maxGeneratedScale - minGeneratedScale) * 2) / (maxHeight / pxStep)
    factorGenerated = 10**int(math.floor(math.log10(rawStepGenerated)))
    endGenerated = rawStepGenerated / factorGenerated
    newEndGenerated = 1
    if endGenerated >= 2:
        newEndGenerated = 2
    if endGenerated >= 5:
        newEndGenerated = 5
    stepGenerated = newEndGenerated * factorGenerated
    rawStepUsed = ((maxUsedScale - minUsedScale) * 2) / (maxHeight / pxStep)
    factorUsed = 10**int(math.floor(math.log10(rawStepUsed)))
    endUsed = rawStepUsed / factorUsed
    newEndUsed = 1
    if endUsed >= 2:
        newEndUsed = 2
    if endUsed >= 5:
        newEndUsed = 5
    stepUsed = newEndUsed * factorUsed
    rawStepDisplaced = ((maxDisplacedScale - minDisplacedScale) * 2) / (maxHeight / pxStep)
    factorDisplaced = 10**int(math.floor(math.log10(rawStepDisplaced)))
    endDisplaced = rawStepDisplaced / factorDisplaced
    newEndDisplaced = 1
    if endDisplaced >= 2:
        newEndDisplaced = 2
    if endDisplaced >= 5:
        newEndDisplaced = 5
    stepDisplaced = newEndDisplaced * factorDisplaced
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter(str(stepUsed) + " " + str(stepExported) + " " + str(stepDisplaced) + " " + str(stepImported) + " " + str(stepGenerated))
if len(resultData) > 0:
    graphLeft = 100
    image = java.awt.image.BufferedImage(graphLeft + len(resultData) + 100, ((maxHeight + 140) * 5) + 100,java.awt.image.BufferedImage.TYPE_4BYTE_ABGR)
    graphics = image.createGraphics()
    defaultFont = graphics.getFont()
    smallFont = java.awt.Font(defaultFont.getName(), defaultFont.getStyle(), 10)
    scaleFactorExported = float(maxHeight) / (maxExportedScale - minExportedScale)
    scaleFactorImported = float(maxHeight) / (maxImportedScale - minImportedScale)
    scaleFactorGenerated = float(maxHeight) / (maxGeneratedScale - minGeneratedScale)
    scaleFactorUsed = float(maxHeight) / (maxUsedScale - minUsedScale)
    scaleFactorDisplaced = float(maxHeight) / (maxDisplacedScale - minDisplacedScale)
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter(str(scaleFactorExported) + " " + str(scaleFactorUsed) + " " + str(scaleFactorDisplaced) + " " + str(scaleFactorImported) + " " + str(scaleFactorGenerated))
    graphOrderExported = 5
    graphOrderImported = 4
    graphOrderGenerated = 3
    graphOrderUsed = 1
    graphOrderDisplaced = 2
    graphTopExported = ((graphOrderExported - 1) * (maxHeight + 150)) + 100
    graphTopImported = ((graphOrderImported - 1) * (maxHeight + 150)) + 100
    graphTopGenerated = ((graphOrderGenerated - 1) * (maxHeight + 150)) + 100
    graphTopUsed = ((graphOrderUsed - 1) * (maxHeight + 150)) + 100
    graphTopDisplaced = ((graphOrderDisplaced - 1) * (maxHeight + 150)) + 100
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter(str(graphTopExported) + " " + str(graphTopImported) + " " + str(graphTopUsed) + " " + str(graphTopDisplaced))
    xAxisExported = int(graphTopExported + maxExportedScale * scaleFactorExported)
    xAxisImported = int(graphTopImported + maxImportedScale * scaleFactorImported)
    xAxisGenerated = int(graphTopGenerated + maxGeneratedScale * scaleFactorGenerated)
    xAxisUsed = int(graphTopUsed + maxUsedScale * scaleFactorUsed)
    xAxisDisplaced = int(graphTopDisplaced + maxDisplacedScale * scaleFactorDisplaced)
    monthDateFormat = java.text.DateFormat.getDateInstance(java.text.DateFormat.LONG, java.util.Locale.UK)
    monthDateFormat.applyLocalizedPattern("MMMMMM")
    yearDateFormat = java.text.DateFormat.getDateInstance(java.text.DateFormat.LONG, java.util.Locale.UK)
    yearDateFormat.applyLocalizedPattern("yyyy")
    monthPoints = []
    for i in range(len(resultData)):
        dataHh = resultData[i]
        date = dataHh[0]
        usedValue = dataHh[2]
        displacedValue = dataHh[3]
        dataHhSupplyList = dataHh[1]
        cal.setTimeInMillis(date)
        hour = cal.get(java.util.Calendar.HOUR_OF_DAY)
        minute = cal.get(java.util.Calendar.MINUTE)
        for j in dataHhSupplyList:
            source = j[1]
            isImport = j[2]
            value = j[3]
            graphics.setColor(java.awt.Color.BLUE)
            if  source == "net" and not isImport:
                height = int(value * scaleFactorExported)
                graphics.fillRect(graphLeft + i, xAxisExported - height, 1, height)
            if  source == "net" and isImport:
                height = int(value * scaleFactorImported)
                graphics.fillRect(graphLeft + i, xAxisImported - height, 1, height)
            if date == 1167757200000L:
                if sourceCode == "lm":
                    raise net.sf.chellow.monad.ui.UserException.newInvalidParameter("is is lm " + str(isImport) + " " + str(sourceCode) + " " + str(dataHhSupplyList))


            if isImport and (sourceCode == "lm" or sourceCode == "chp" or sourceCode == "turb"):
                height = int(value * scaleFactorGenerated)
                graphics.fillRect(graphLeft + i, xAxisGenerated - height, 1, height)
        usedHeight = int(usedValue * scaleFactorUsed)
        if usedHeight < 0:
            graphics.fillRect(graphLeft + i, xAxisUsed, 1, abs(usedHeight))
        else:
            graphics.fillRect(graphLeft + i, xAxisUsed - usedHeight, 1, usedHeight)
        displacedHeight = int(displacedValue * scaleFactorDisplaced)
        if displacedHeight < 0:
            graphics.fillRect(graphLeft + i, xAxisDisplaced, 1, abs(displacedHeight))        
        else:
            graphics.fillRect(graphLeft + i, xAxisDisplaced - displacedHeight, 1, displacedHeight)
        if hour == 0 and minute == 30:
            day = cal.get(java.util.Calendar.DAY_OF_MONTH)
            dayOfWeek = cal.get(java.util.Calendar.DAY_OF_WEEK)
            if dayOfWeek == 7 or dayOfWeek == 1:
                graphics.setColor(java.awt.Color.RED)
            else:
                graphics.setColor(java.awt.Color.BLACK)
            graphics.drawString(str(day), graphLeft + i + 16, graphTopExported + maxHeight + 20)
            graphics.drawString(str(day), graphLeft + i + 16, graphTopImported + maxHeight + 20)
            graphics.drawString(str(day), graphLeft + i + 16, graphTopGenerated + maxHeight + 20)
            graphics.drawString(str(day), graphLeft + i + 16, graphTopUsed + maxHeight + 20)
            graphics.drawString(str(day), graphLeft + i + 16, graphTopDisplaced + maxHeight + 20)
            graphics.setColor(java.awt.Color.BLACK)
            graphics.fillRect(graphLeft + i, graphTopExported + maxHeight, 1, 5)
            graphics.fillRect(graphLeft + i, graphTopImported + maxHeight, 1, 5)
            graphics.fillRect(graphLeft + i, graphTopGenerated + maxHeight, 1, 5)
            graphics.fillRect(graphLeft + i, graphTopUsed + maxHeight, 1, 5)
            graphics.fillRect(graphLeft + i, graphTopDisplaced + maxHeight, 1, 5)
            if day == 15:
                graphics.drawString(monthDateFormat.format(cal.getTime()), graphLeft + i + 16, graphTopExported + maxHeight + 45)
                graphics.drawString(monthDateFormat.format(cal.getTime()), graphLeft + i + 16, graphTopImported + maxHeight + 45)
                graphics.drawString(monthDateFormat.format(cal.getTime()), graphLeft + i + 16, graphTopGenerated + maxHeight + 45)
                graphics.drawString(monthDateFormat.format(cal.getTime()), graphLeft + i + 16, graphTopUsed + maxHeight + 45)
                graphics.drawString(monthDateFormat.format(cal.getTime()), graphLeft + i + 16, graphTopDisplaced + maxHeight + 45)
                monthPoints.append(i)
    graphics.setColor(java.awt.Color.BLACK)
    graphics.fillRect(graphLeft, graphTopExported, 1, maxHeight)
    graphics.fillRect(graphLeft, graphTopImported, 1, maxHeight)
    graphics.fillRect(graphLeft, graphTopGenerated, 1, maxHeight)
    graphics.fillRect(graphLeft, graphTopUsed, 1, maxHeight)
    graphics.fillRect(graphLeft, graphTopDisplaced, 1, maxHeight)
    scalePointsExported = []
    for i in range(0, int(maxExportedScale), stepExported):
        scalePointsExported.append(i)
    for i in range(0, int(minExportedScale), stepExported * -1):
        scalePointsExported.append(i)
    graphics.setColor(java.awt.Color.BLACK)
    for point in scalePointsExported:
        graphics.fillRect(graphLeft - 5, int(xAxisExported - point * scaleFactorExported), len(resultData) + 5, 1)
        graphics.drawString(str(point * 2), graphLeft - 40, int(xAxisExported - point * scaleFactorExported + 5))
        for monthPoint in monthPoints:
            graphics.drawString(str(point * 2), graphLeft + monthPoint + 16, int(xAxisExported - point * scaleFactorExported - 2))
    scalePointsImported = []
    for i in range(0, int(maxImportedScale), stepImported):
        scalePointsImported.append(i)
    for i in range(0, int(minImportedScale), stepImported * -1):
        scalePointsImported.append(i)
    graphics.setColor(java.awt.Color.BLACK)
    for point in scalePointsImported:
        graphics.fillRect(graphLeft - 5, int(xAxisImported - point * scaleFactorImported), len(resultData) + 5, 1)
        graphics.drawString(str(point * 2), graphLeft - 40, int(xAxisImported - point * scaleFactorImported + 5))
        for monthPoint in monthPoints:
            graphics.drawString(str(point * 2), graphLeft + monthPoint + 16, int(xAxisImported - point * scaleFactorImported - 2))
    scalePointsGenerated = []
    for i in range(0, int(maxGeneratedScale), stepGenerated):
        scalePointsGenerated.append(i)
    for i in range(0, int(minGeneratedScale), stepGenerated * -1):
        scalePointsGenerated.append(i)
    graphics.setColor(java.awt.Color.BLACK)
    for point in scalePointsGenerated:
        graphics.fillRect(graphLeft - 5, int(xAxisGenerated - point * scaleFactorGenerated), len(resultData) + 5, 1)
        graphics.drawString(str(point * 2), graphLeft - 40, int(xAxisGenerated - point * scaleFactorGenerated + 5))
        for monthPoint in monthPoints:
            graphics.drawString(str(point * 2), graphLeft + monthPoint + 16, int(xAxisGenerated - point * scaleFactorGenerated - 2))
    scalePointsUsed = []
    for i in range(0, int(maxUsedScale), stepUsed):
        scalePointsUsed.append(i)
    for i in range(0, int(minUsedScale), stepUsed * -1):
        scalePointsUsed.append(i)
    for point in scalePointsUsed:
        graphics.fillRect(graphLeft - 5, int(xAxisUsed - point * scaleFactorUsed), len(resultData) + 5, 1)
        graphics.drawString(str(point * 2), graphLeft - 40, int(xAxisUsed - point * scaleFactorUsed + 5))
        for monthPoint in monthPoints:
            graphics.drawString(str(point * 2), graphLeft + monthPoint + 16, int(xAxisUsed - point * scaleFactorUsed - 2))
    scalePointsDisplaced = []
    for i in range(0, int(maxDisplacedScale), stepDisplaced):
        scalePointsDisplaced.append(i)
    for i in range(0, int(minDisplacedScale), stepDisplaced * -1):
        scalePointsDisplaced.append(i)
    for point in scalePointsDisplaced:
        graphics.fillRect(graphLeft - 5, int(xAxisDisplaced - point * scaleFactorDisplaced), len(resultData) + 5, 1)
        graphics.drawString(str(point * 2), graphLeft - 40, int(xAxisDisplaced - point * scaleFactorDisplaced + 5))
        for monthPoint in monthPoints:
            graphics.drawString(str(point * 2), graphLeft + monthPoint + 16, int(xAxisDisplaced - point * scaleFactorDisplaced - 2))
    graphics.drawString("kW", graphLeft - 90, graphTopExported + 50)
    graphics.drawString("kW", graphLeft - 90, graphTopImported + 50)
    graphics.drawString("kW", graphLeft - 90, graphTopGenerated + 50)
    graphics.drawString("kW", graphLeft - 90, graphTopUsed + 50)
    graphics.drawString("kW", graphLeft - 90, graphTopDisplaced + 50)
    title = "Electricity generation at site " + site.getCode().toString() + " " + site.getName().toString() + " for " + str(months) + " month"
    if months > 1:
        title = title + "s"
    title = title + " ending " + monthDateFormat.format(java.util.Date(finishDate.getTime() - 1)) + " " + yearDateFormat.format(java.util.Date(finishDate.getTime() - 1))
    graphics.drawString(title, 30, 40)
    graphics.drawString("Imported", 40, graphTopImported - 20)
    graphics.drawString("Exported", 40, graphTopExported - 20)
    graphics.drawString("Generated", 40, graphTopGenerated - 20)
    graphics.drawString("Used", 40, graphTopUsed - 20)
    graphics.drawString("Displaced", 40, graphTopDisplaced - 20)
    graphics.setFont(smallFont)
    graphics.drawString("Poor data is denoted by a grey background and black foreground.", 30, graphTopExported + maxHeight + 45)
    graphics.drawString("Poor data is denoted by a grey background and black foreground.", 30, graphTopImported + maxHeight + 45)
    graphics.drawString("Poor data is denoted by a grey background and black foreground.", 30, graphTopGenerated + maxHeight + 45)
    graphics.drawString("Poor data is denoted by a grey background and black foreground.", 30, graphTopUsed + maxHeight + 45)
    graphics.drawString("Poor data is denoted by a grey background and black foreground.", 30, graphTopDisplaced + maxHeight + 45)
else:
    image = java.awt.image.BufferedImage(400, 400,java.awt.image.BufferedImage.TYPE_4BYTE_ABGR)
    graphics = image.createGraphics()
    graphics.setColor(java.awt.Color.BLACK)
    graphics.drawString("No data available for this period.", 30, 10)

os = inv.getResponse().getOutputStream()
graphics.setColor(java.awt.Color.BLACK)
#graphics.drawString("report took..." + str(java.lang.System.currentTimeMillis() - start) + "ms", 10, 390)
javax.imageio.ImageIO.write(image, "png", os)
os.close()