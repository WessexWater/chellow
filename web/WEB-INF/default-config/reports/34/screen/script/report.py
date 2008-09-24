from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import RateScript

script_id = inv.getLong('dso-rate-script-id')
script = RateScript.getRateScript(script_id)
source.appendChild(script.toXml(doc, XmlTree('service', XmlTree('dso'))))
source.appendChild(organization.toXml(doc))