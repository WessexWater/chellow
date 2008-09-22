from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.data08 import MpanCoreTerm

if inv.hasParameter('search-pattern'):
    search_pattern = MpanCoreTerm(inv.getString('search-pattern'))
    for mpan_core_list in Hiber.session().createQuery("select distinct mpanCore, mpanCore.dso.code, mpanCore.uniquePart, mpanCore.checkDigit from MpanCore mpanCore where mpanCore.supply.organization = :organization and lower(mpanCore.dso.code || mpanCore.uniquePart || mpanCore.checkDigit) like lower(:term) order by mpanCore.dso.code, mpanCore.uniquePart, mpanCore.checkDigit").setEntity("organization", organization).setString("term","%" + search_pattern.toString() + "%").setMaxResults(50).list():
        source.appendChild(mpan_core_list[0].toXml(doc, XmlTree("supply").put("dso")))
source.appendChild(organization.toXml(doc))
