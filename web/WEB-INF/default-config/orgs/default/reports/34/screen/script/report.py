from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import RateScript

script_id = inv.getLong('dso-rate-script-id')
script = RateScript.getRateScript(script_id)
source.appendChild(script.toXml(XmlTree('service', XmlTree('provider')), doc))
source.appendChild(organization.toXml(doc))