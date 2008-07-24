from net.sf.chellow.monad import Hiber

for participant in Hiber.session().createQuery('from Participant participant order by participant.code').list():
    source.appendChild(participant.toXml(doc))
source.appendChild(organization.toXml(doc))

