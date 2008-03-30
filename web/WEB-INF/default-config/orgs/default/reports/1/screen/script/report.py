from net.sf.chellow.monad import Hiber

for site in Hiber.session().createQuery("select distinct site from Site site join site.siteSupplyGenerations siteSupplyGeneration where site.organization = :organization").setEntity("organization", organization).list():
    source.appendChild(site.toXML(doc))
