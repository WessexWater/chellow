from net.sf.chellow.monad import Hiber

if inv.hasParameter('search-pattern'):
    search_pattern = inv.getString('search-pattern')
    for site in organization.findSites(search_pattern):
        source.appendChild(site.toXML(doc))
source.appendChild(organization.toXML(doc))
