from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import HhdcContract

contract_id = inv.getLong('hhdc-contract-id')
contract = HhdcContract.getHhdcContract(contract_id)
snags = Hiber.session().createQuery("select snag, snag.site from SiteSnag snag where snag.site.organization = :organization and snag.dateResolved is null and snag.contract = :contract order by snag.site.code, snag.startDate.date").setEntity("organization", organization).setEntity('contract', contract).list()
snags_element = doc.createElement('site-snags')
source.appendChild(snags_element)
snags_element.appendChild(contract.toXml(doc, XmlTree('provider').put('organization')))
for snag_row in snags:
    snag_element = snag_row[0].toXml(doc)
    snags_element.appendChild(snag_element)
    site_element = snag_row[1].toXml(doc)
    snag_element.appendChild(site_element)

sites = Hiber.session().createQuery("select count(distinct snag.site) from SiteSnag snag where snag.site.organization = :organization and snag.contract = :contract and snag.dateResolved is null").setEntity("organization", organization).setEntity('contract', contract).uniqueResult()

snags_element.setAttribute("snag-count", str(len(snags)))
snags_element.setAttribute("site-count", str(sites))
