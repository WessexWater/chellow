from net.sf.chellow.monad import XmlTree, Hiber
from java.util import Date
from java.lang import System
from net.sf.chellow.physical import SiteCode

dceId = inv.getLong('dce-id')
if not inv.isValid():
    raise UserError()
snags = Hiber.session().createQuery("select distinct snag, snag.channel, snag.channel.supply, siteSupplyGeneration.site from SnagChannel snag join snag.channel.supply.generations generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and snag.dateResolved is null and snag.service.provider.id = :providerId and snag.startDate.date < :activeDate order by siteSupplyGeneration.site.code, snag.startDate.date, snag.channel.id").setEntity("organization", organization).setLong("providerId", dceId).setTimestamp("activeDate",Date(System.currentTimeMillis()-(5*24*60*60*1000))).list()

for snagRow in snags:
    snagElement = snagRow[0].toXML(doc)
    source.appendChild(snagElement)
    channelElement = snagRow[1].toXML(doc)
    snagElement.appendChild(channelElement)
    supplyElement = snagRow[2].getXML(XmlTree("generationLast",XmlTree("mpans",XmlTree("mpanCore",XmlTree("dso")))),doc)
    supplyElement.appendChild(snagRow[3].toXML(doc))
    channelElement.appendChild(supplyElement)

activeSites = Hiber.session().createQuery("select count(distinct siteSupplyGeneration.site) from SnagChannel snag join snag.channel.supply.generations generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and snag.dateResolved is null and snag.service.provider.id = :providerId and snag.startDate.date < :activeDate").setEntity("organization", organization).setLong("providerId", dceId).setTimestamp("activeDate",Date(System.currentTimeMillis()-(5*24*60*60*1000))).uniqueResult()

totalSites = Hiber.session().createQuery("select count(distinct siteSupplyGeneration.site) from SnagChannel snag join snag.channel.supply.generations generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and snag.dateResolved is null and snag.service.provider.id = :providerId").setEntity("organization", organization).setLong("providerId", dceId).uniqueResult()

source.setAttribute("snag-count", str(len(snags)))
source.setAttribute("site-count", str(activeSites))
source.setAttribute("pending-site-count",str(totalSites-activeSites))