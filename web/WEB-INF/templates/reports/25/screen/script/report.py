from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import Llfc

llfc_id = inv.getLong('llfc-id')
llfc = Llfc.getLlfc(llfc_id)
source.appendChild(llfc.toXml(doc, XmlTree('dso').put('voltageLevel')))
source.appendChild(organization.toXml(doc))

