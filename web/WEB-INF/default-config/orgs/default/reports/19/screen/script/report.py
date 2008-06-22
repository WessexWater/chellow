from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import DceService

service_id = inv.getLong('service-id')
service = DceService.getDceService(service_id)
snags = Hiber.session().createQuery("select snag, snag.site from SiteSnag snag where snag.site.organization = :organization and snag.dateResolved is null and snag.service = :dceService order by snag.site.code, snag.startDate.date").setEntity("organization", organization).setEntity('dceService', service).list()
snags_element = doc.createElement('site-snags')
source.appendChild(snags_element)
snags_element.appendChild(service.toXml(doc, XmlTree('provider', XmlTree('organization'))))
for snag_row in snags:
    snag_element = snag_row[0].toXml(doc)
    snags_element.appendChild(snag_element)
    site_element = snag_row[1].toXml(doc)
    snag_element.appendChild(site_element)

sites = Hiber.session().createQuery("select count(distinct snag.site) from SiteSnag snag where snag.site.organization = :organization and snag.service = :dceService and snag.dateResolved is null").setEntity("organization", organization).setEntity('dceService', service).uniqueResult()

snags_element.setAttribute("snag-count", str(len(snags)))
snags_element.setAttribute("site-count", str(sites))
