from net.sf.chellow.monad import Hiber, XmlTree

contracts_element = doc.createElement('contracts')
source.appendChild(contracts_element)
for contract in Hiber.session().createQuery("from HhdcContract contract where contract.organization = :organization order by contract.startRateScript.startDate.date").setEntity("organization", organization).list():
    contract_element = contract.toXml(doc, XmlTree('provider'))
    contracts_element.appendChild(contract_element)
    start_rate_script = contract.getStartRateScript()
    start_rate_script.setLabel('start')
    contract_element.appendChild(start_rate_script.toXml(doc))
    finish_rate_script = contract.getFinishRateScript()
    finish_rate_script.setLabel('finish')
    contract_element.appendChild(finish_rate_script.toXml(doc))
contracts_element.appendChild(organization.toXml(doc))