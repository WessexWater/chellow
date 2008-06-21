from net.sf.chellow.monad import Hiber

for dso in Hiber.session().createQuery(
                'from Dso dso order by dso.code.string').list():
    source.appendChild(dso.toXml(doc));
source.appendChild(organization.toXml(doc))

