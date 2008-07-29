from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import Ssc

ssc_id = inv.getLong('ssc-id')
ssc = Ssc.getSsc(ssc_id)
source.appendChild(ssc.toXml(doc, XmlTree("measurementRequirements", XmlTree("tpr"))))
source.appendChild(organization.toXml(doc))