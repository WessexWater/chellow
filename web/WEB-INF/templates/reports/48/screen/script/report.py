from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import Tpr

tpr_id = inv.getLong('tpr-id')
tpr = Tpr.getTpr(tpr_id)
source.appendChild(tpr.toXml(doc, XmlTree("measurementRequirements", XmlTree("ssc")).put("clockIntervals")))
source.appendChild(organization.toXml(doc))