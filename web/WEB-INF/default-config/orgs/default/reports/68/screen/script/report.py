from net.sf.chellow.monad import Hiber, XmlTree

for dso in Hiber.session().createQuery(
                'from Dso dso order by dso.code.string').list():
    source.appendChild(dso.toXml(doc, XmlTree('participant').put('role')));
source.appendChild(organization.toXml(doc))

