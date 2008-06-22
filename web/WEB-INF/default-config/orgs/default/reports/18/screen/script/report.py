from net.sf.chellow.monad import XmlTree, Hiber
from java.util import Date
from java.lang import System
from net.sf.chellow.physical import SiteCode
from net.sf.chellow.billing import DceService

service_id = inv.getLong('service-id')
if not inv.isValid():
    raise UserException()
service = DceService.getDceService(service_id)
snags_element = doc.createElement('channel-snags')
source.appendChild(snags_element)
snags_element.appendChild(service.toXml(doc, XmlTree('provider', XmlTree('organization'))))
snags = Hiber.session().createQuery("select distinct snag, snag.channel, snag.channel.supply, siteSupplyGeneration.site from ChannelSnag snag join snag.channel.supply.generations generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and snag.dateResolved is null and snag.service = :service and snag.startDate.date < :activeDate order by siteSupplyGeneration.site.code, snag.startDate.date, snag.channel.id").setEntity("organization", organization).setEntity('service', service).setTimestamp("activeDate",Date(System.currentTimeMillis()-(5*24*60*60*1000))).list()
for snag_row in snags:
    snagElement = snag_row[0].toXml(doc)
    snags_element.appendChild(snagElement)
    channelElement = snag_row[1].toXml(doc)
    snagElement.appendChild(channelElement)
    supplyElement = snag_row[2].toXml(doc, XmlTree("generationLast",XmlTree("mpans",XmlTree("mpanCore",XmlTree("dso")))))
    supplyElement.appendChild(snag_row[3].toXml(doc))
    channelElement.appendChild(supplyElement)

activeSites = Hiber.session().createQuery("select count(distinct siteSupplyGeneration.site) from ChannelSnag snag join snag.channel.supply.generations generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and snag.dateResolved is null and snag.service = :service and snag.startDate.date < :activeDate").setEntity('organization', organization).setEntity('service', service).setTimestamp("activeDate",Date(System.currentTimeMillis()-(5*24*60*60*1000))).uniqueResult()
totalSites = Hiber.session().createQuery("select count(distinct siteSupplyGeneration.site) from ChannelSnag snag join snag.channel.supply.generations generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and snag.dateResolved is null and snag.service = :service").setEntity('organization', organization).setEntity('service', service).uniqueResult()

snags_element.setAttribute("snag-count", str(len(snags)))
snags_element.setAttribute("site-count", str(activeSites))
snags_element.setAttribute("pending-site-count", str(totalSites - activeSites))