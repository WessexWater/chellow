from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import Llf

llf_id = inv.getLong('llf-id')
llf = Llf.getLlf(llf_id)
source.appendChild(llf.getXML(XmlTree('dso').put('voltageLevel'), doc))
source.appendChild(organization.toXML(doc))

