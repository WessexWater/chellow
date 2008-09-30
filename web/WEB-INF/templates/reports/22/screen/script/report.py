from net.sf.chellow.monad import Hiber, XmlTree

for provider in Hiber.session().createQuery(
                'from Provider provider order by provider.participant.code, provider.role.code').list():
    source.appendChild(provider.toXml(doc, XmlTree('participant').put('role')));
source.appendChild(organization.toXml(doc))

