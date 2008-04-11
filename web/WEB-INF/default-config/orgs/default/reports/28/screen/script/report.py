from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import Dso

dso_id = inv.getLong('dso-id')
dso = Dso.getDso(dso_id)
mpan_tops_element = doc.createElement('mpan-tops')
source.appendChild(mpan_tops_element)
for mpan_top in Hiber.session().createQuery("from MpanTop mpanTop where mpanTop.llf.dso = :dso order by mpanTop.profileClass.code.integer, mpanTop.llf.code.integer, mpanTop.meterTimeswitch.code.integer").setEntity("dso", dso).list():
    mpan_tops_element.appendChild(mpan_top.getXML(XmlTree("profileClass").put("llf").put("meterTimeswitch"), doc))
mpan_tops_element.appendChild(dso.toXML(doc));
source.appendChild(organization.toXML(doc))