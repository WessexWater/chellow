from net.sf.chellow.monad import XmlTree, Hiber
from java.util import Date
from java.lang import System
from net.sf.chellow.billing import HhdcContract

contract_id = inv.getLong('hhdc-contract-id')
if not inv.isValid():
    raise UserException()
contract = HhdcContract.getHhdcContract(contract_id)
snags_element = doc.createElement('channel-snags')
source.appendChild(snags_element)
snags_element.appendChild(contract.toXml(doc, XmlTree('provider').put('organization'))) 
#for snag_row in Hiber.session().createQuery("select distinct snag from ChannelSnag snag join snag.channel.supplyGeneration.siteSupplyGenerations siteSupplyGeneration where snag.channel.supplyGeneration.supply.organization = :organization and snag.dateResolved is null and snag.contract = :contract and snag.startDate.date < :activeDate order by siteSupplyGeneration.site.code, snag.startDate.date, snag.channel.id").setEntity("organization", organization).setEntity('contract', contract).setTimestamp("activeDate",Date(System.currentTimeMillis()-(5*24*60*60*1000))).list():
snags = Hiber.session().createQuery("select distinct snag, siteSupplyGeneration.site.code, snag.startDate.date, snag.channel.id from ChannelSnag snag join snag.channel.supplyGeneration.siteSupplyGenerations siteSupplyGeneration where snag.channel.supplyGeneration.supply.organization = :organization and snag.dateResolved is null and snag.contract = :contract and snag.startDate.date < :activeDate order by siteSupplyGeneration.site.code, snag.startDate.date, snag.channel.id").setEntity("organization", organization).setEntity('contract', contract).setTimestamp("activeDate",Date(System.currentTimeMillis()-(5*24*60*60*1000))).list()
for snag_row in snags:
    snags_element.appendChild(snag_row[0].toXml(doc, XmlTree('channel', XmlTree('supplyGeneration', XmlTree('supply').put('siteSupplyGenerations', XmlTree('site')).put("mpans", XmlTree("mpanCore", XmlTree("dso")))))))
activeSites = Hiber.session().createQuery("select count(distinct siteSupplyGeneration.site) from ChannelSnag snag join snag.channel.supplyGeneration.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and snag.dateResolved is null and snag.contract = :contract and snag.startDate.date < :activeDate").setEntity('organization', organization).setEntity('contract', contract).setTimestamp("activeDate",Date(System.currentTimeMillis()-(5*24*60*60*1000))).uniqueResult()
totalSites = Hiber.session().createQuery("select count(distinct siteSupplyGeneration.site) from ChannelSnag snag join snag.channel.supplyGeneration.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and snag.dateResolved is null and snag.contract = :contract").setEntity('organization', organization).setEntity('contract', contract).uniqueResult()

snags_element.setAttribute("snag-count", str(len(snags)))
snags_element.setAttribute("site-count", str(activeSites))
snags_element.setAttribute("pending-site-count", str(totalSites - activeSites))