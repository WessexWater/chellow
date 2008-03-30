import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import net.sf.chellow.monad.vf.bo

snags = net.sf.chellow.persistant08.Hiber.session().createQuery("select snag,snag.channel,snag.channel.supply,siteSupply.site from SnagChannel snag join snag.channel.supply.siteSupplies as siteSupply where siteSupply.site.organization = :organization and snag.dateResolved.date is null and snag.contract.supplier.id = :supplierId order by siteSupply.site.id,snag.channel.supply.id,snag.channel.id,snag.id").setEntity("organization", organization).setLong("supplierId", 1).setMaxResults(20).list()

for snagRow in snags:
    snagElement = snagRow[0].toXML(doc)
    source.appendChild(snagElement)
    channelElement = snagRow[1].toXML(doc)
    snagElement.appendChild(channelElement)
    supplyElement = snagRow[2].getXML(net.sf.chellow.monad.vf.bo.XMLTree("generationLast",net.sf.chellow.monad.vf.bo.XMLTree("mpans",net.sf.chellow.monad.vf.bo.XMLTree("mpanCore",net.sf.chellow.monad.vf.bo.XMLTree("dso")))),doc)
    supplyElement.appendChild(snagRow[3].toXML(doc))
    channelElement.appendChild(supplyElement)
    
