from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import Dso

dso_id = inv.getLong('dso-id')
dso = Dso.getDso(dso_id)
mpan_tops_element = doc.createElement('mpan-tops')
source.appendChild(mpan_tops_element)
for mpan_top in Hiber.session().createQuery("from MpanTop mpanTop where mpanTop.llfc.dso = :dso order by mpanTop.pc.code.integer, mpanTop.llfc.code.integer, mpanTop.mtc.code.integer").setEntity("dso", dso).list():
    mpan_tops_element.appendChild(mpan_top.toXml(doc, XmlTree("pc").put("llfc").put("mtc").put("ssc")))
mpan_tops_element.appendChild(dso.toXml(doc));
source.appendChild(organization.toXml(doc))