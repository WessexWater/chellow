from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.data08 import MpanCoreTerm

if inv.hasParameter('search-pattern'):
    search_pattern = MpanCoreTerm(inv.getString('search-pattern'))
    for mpan_core_list in Hiber.session().createQuery("select distinct mpanCore,mpanCore.dso.code.string, mpanCore.uniquePart.string, mpanCore.checkDigit.character from MpanCore mpanCore join mpanCore.supply.generations supplyGeneration join supplyGeneration.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and lower(mpanCore.dso.code.string || mpanCore.uniquePart.string || mpanCore.checkDigit.character) like lower(:term) order by mpanCore.dso.code.string, mpanCore.uniquePart.string, mpanCore.checkDigit.character").setEntity("organization", organization).setString("term","%" + search_pattern.toString() + "%").setMaxResults(50).list():
        source.appendChild(mpan_core_list[0].getXML(XmlTree("supply").put("dso"), doc))
source.appendChild(organization.toXML(doc))
