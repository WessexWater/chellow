import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui

sites = net.sf.chellow.persistant08.Hiber.session().createQuery("select distinct site from Site site join site.siteSupplies as siteSupply where site.organization = :organization").setEntity("organization", organization).list()

for site in sites:
    source.appendChild(site.toXml(doc))
