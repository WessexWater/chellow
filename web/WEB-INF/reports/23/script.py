import sys
from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'utils', 'db')

if sys.platform.startswith('java'):
    from java.awt.image import BufferedImage
    from javax.imageio import ImageIO
    from java.awt import Color, Font
    from java.lang import System
    import math
    import datetime
    import pytz
    from dateutil.relativedelta import relativedelta

    HH = utils.HH
    Site = db.Site

    colour_list = [
        Color.BLUE, Color.GREEN, Color.RED, Color.YELLOW, Color.MAGENTA,
        Color.CYAN, Color.PINK, Color.ORANGE]

    def set_colour(graphics, supplies, id):
        graphics.setColor(supplies[id][0])

    def add_colour(supplies, id, name, source_code):
        if not id in supplies:
            supplies[id] = [len(supplies), name, source_code]

    def sort_colour(supplies):
        keys = supplies.keys()
        keys.sort()
        for i in range(len(keys)):
            supplies[keys[i]][0] = colour_list[i]

    def paint_legend(supplies, graph_top):
        i = 0
        keys = supplies.keys()
        keys.sort()
        for key in keys:
            supply = supplies[key]
            graphics.setColor(supply[0])
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

    sess = None
    try:
        sess = db.session()

        start = System.currentTimeMillis()
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

        generated_supplies = {}
        imported_supplies = {}
        exported_supplies = {}
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
        actualStatus = 'A'

        site = Site.get_by_id(sess, site_id)
        hhDate = start_date
        groups = site.groups(sess, start_date, finish_date, True)
        for group in groups:
            rs = iter(sess.execute("select hh_datum.value, hh_datum.start_date, hh_datum.status, channel.imp_related, supply.name, source.code, supply.id as supply_id from hh_datum, channel, era, supply, source where hh_datum.channel_id = channel.id and channel.era_id = era.id and era.supply_id = supply.id and supply.source_id = source.id and channel.channel_type = 'ACTIVE' and hh_datum.start_date >= :start_date and hh_datum.start_date <= :finish_date and supply.id = any(:supply_ids) order by hh_datum.start_date, supply.id", params={'start_date': group.start_date, 'finish_date': group.finish_date, 'supply_ids': [s.id for s in group.supplies]}))

            try:
                row = rs.next()
                hhChannelValue = float(row.value)
                hhChannelStartDate = row.start_date
                imp_related = row.imp_related
                status = row.status
                source_code = row.code
                supply_name = row.name
                supply_id = row.supply_id

                while hhDate <= finish_date:
                    complete = "blank"
                    exportedValue = 0
                    importedValue = 0
                    parasiticValue = 0
                    generatedValue = 0
                    third_party_import = 0
                    third_party_export = 0
                    supplyList = []
                    while hhChannelStartDate == hhDate:
                        if not imp_related and source_code in ('net', 'gen-net'):
                            exportedValue += hhChannelValue
                            add_colour(exported_supplies, supply_id, supply_name, source_code)
                        if imp_related and source_code in ('net', 'gen-net'):
                            importedValue += hhChannelValue
                            add_colour(imported_supplies, supply_id, supply_name, source_code)
                        if (imp_related and source_code == 'gen') or (not imp_related and source_code == 'gen-net'):
                            generatedValue += hhChannelValue
                            add_colour(generated_supplies, supply_id, supply_name, source_code)
                        if (not imp_related and source_code == 'gen') or (imp_related and source_code == 'gen-net'):
                            parasiticValue += hhChannelValue
                            add_colour(generated_supplies, supply_id, supply_name, source_code)
                        supplyList.append([supply_name, source_code, imp_related, hhChannelValue, supply_id])
                        if (imp_related and source_code == '3rd-party') or (not imp_related and source_code == '3rd-party-reverse'):
                            third_party_import += hhChannelValue
                        if (not imp_related and source_code == '3rd-party') or (imp_related and source_code == '3rd-party-reverse'):
                            third_party_export += hhChannelValue
                        try:
                            row = rs.next()
                            source_code = row.code
                            supply_name = row.name
                            hhChannelValue = float(row.value)
                            hhChannelStartDate = row.start_date
                            imp_related = row.imp_related
                            status = row.status
                            supply_id = row.supply_id
                        except StopIteration:
                            hhChannelStartDate = None

                    maxExportedScale = max(maxExportedScale, exportedValue)
                    minExportedScale = min(minExportedScale, exportedValue)
                    maxImportedScale = max(maxImportedScale, importedValue)
                    minImportedScale = min(minImportedScale, importedValue)
                    maxGeneratedScale = max(maxGeneratedScale, generatedValue)
                    maxParasiticScale = max(maxParasiticScale, parasiticValue)
                    displacedValue = generatedValue - parasiticValue - exportedValue
                    maxDisplacedScale = max(maxDisplacedScale, displacedValue)
                    minDisplacedScale = min(minDisplacedScale, displacedValue)
                    usedValue = importedValue + displacedValue + third_party_import - third_party_export
                    maxUsedScale = max(maxUsedScale, usedValue)
                    minUsedScale = min(minUsedScale, usedValue)
                    resultData.append([hhDate, supplyList, usedValue, displacedValue])
                    hhDate += HH
            except StopIteration:
                pass

            #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter("ResultData: " + str(resultData)) 
            #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter("Overall: " + str(maxOverallScale) + " " + str(minOverallScale) + " Exported: " + str(maxExportedScale) + " " + str(minExportedScale) + " Imported: " + str(maxImportedScale) + " " + str(minImportedScale) + " Generated: " + str(maxGeneratedScale) + " Parasitic: " + str(maxParasiticScale) + " Displaced: " + str(maxDisplacedScale) + " " + str(minDisplacedScale) + " Used: " + str(maxUsedScale) + " " + str(minUsedScale))
            sort_colour(generated_supplies)
            sort_colour(imported_supplies)
            sort_colour(exported_supplies)
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
            monthPoints = []
            for i, dataHh in enumerate(resultData):
                date = dataHh[0]
                usedValue = dataHh[2]
                displacedValue = dataHh[3]
                dataHhSupplyList = dataHh[1]

                hour = date.hour
                minute = date.minute
                graphics.setColor(Color.BLUE)
                usedHeight = int(round(usedValue * scaleFactorOverall))
                if usedHeight < 0:
                    graphics.fillRect(graphLeft + i, xAxisUsed, 1, abs(usedHeight))
                else:
                    graphics.fillRect(graphLeft + i, xAxisUsed - usedHeight, 1, usedHeight)
                displacedHeight = int(round(displacedValue * scaleFactorOverall))
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
                    height = int(round(value * scaleFactorOverall))
                    if source in ('net', 'gen-net') and not isImport:
                        set_colour(graphics, exported_supplies, id)
                        exportedTotal = exportedTotal + height
                        graphics.fillRect(graphLeft + i, xAxisExported - exportedTotal, 1, height)
                    if source in ('net', 'gen-net') and isImport:
                        set_colour(graphics, imported_supplies, id)
                        importedTotal = importedTotal + height
                        graphics.fillRect(graphLeft + i, xAxisImported - importedTotal, 1, height)
                    if (isImport and source == 'gen') or (not isImport and source == 'gen-net'):
                        set_colour(graphics, generated_supplies, id)
                        generatedTotal = generatedTotal + height
                        graphics.fillRect(graphLeft + i, xAxisGenerated - generatedTotal, 1, height)
                    if (not isImport and source == 'gen') or (isImport and source == 'gen-net'):
                        set_colour(graphics, generated_supplies, id)
                        parasiticTotal = parasiticTotal + height
                        graphics.fillRect(graphLeft + i, xAxisGenerated, 1, height)
                if hour == 0 and minute == 0:
                    day = date.day
                    dayOfWeek = date.weekday()
                    if dayOfWeek > 4:
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
                        graphics.drawString(date.strftime("%B"), graphLeft + i + 16, ((maxHeight + 22) * 5) + 50 + minUsed + minDisplaced + minParasitic)
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
            title = "Electricity at site " + site.code + " " + site.name + " for " + str(months) + " month"
            if months > 1:
                title = title + "s"
            title = title + " up to and including " + (finish_date - HH).strftime("%B %Y")
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
        #graphics.drawString("report took..." +     str(java.lang.System.currentTimeMillis() - start) + "ms", 10, 390)
        ImageIO.write(image, "png", os)
        os.close()
    finally:
        if sess is not None:
            sess.close()
else:
    from flask import Response

    inv.response = Response("Stub", status=200)
