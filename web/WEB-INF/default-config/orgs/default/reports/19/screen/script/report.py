from net.sf.chellow.monad import Hiber

activeSnags = Hiber.session().createQuery("select snag,snag.site from SnagSite snag where snag.site.organization = :organization and snag.dateResolved is null order by snag.site.code, snag.startDate.date").setEntity("organization", organization).list()

for snagRow in activeSnags:
    snagElement = snagRow[0].toXml(doc)
    source.appendChild(snagElement)
    siteElement = snagRow[1].toXml(doc)
    snagElement.appendChild(siteElement)

activeSites = Hiber.session().createQuery("select count(distinct snag.site) from SnagSite snag where snag.site.organization = :organization and snag.dateResolved is null").setEntity("organization", organization).uniqueResult()

source.setAttribute("snag-count", str(len(activeSnags)))
source.setAttribute("site-count", str(activeSites))

'''
totalSites = Hiber.session().createQuery("select count(distinct siteSupply.site) from SnagChannel snag join snag.channel.supply.siteSupplies as siteSupply where siteSupply.site.organization = :organization and snag.dateResolved is null and snag.contract.supplier.id = :supplierId").setEntity("organization", organization).setLong("supplierId", 1).uniqueResult()

source.setAttribute("pending-site-count",str(totalSites-activeSites))
''' 
