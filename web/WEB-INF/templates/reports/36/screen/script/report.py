from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import Participant

participant_id = inv.getLong('participant-id')
participant = Participant.getParticipant(participant_id)
participant_element = participant.toXml(doc)
source.appendChild(participant_element);
for provider in Hiber.session().createQuery("from Provider provider where provider.participant = :participant order by provider.role.code").setEntity('participant', participant).list():
    participant_element.appendChild(provider.toXml(doc, XmlTree('role')))
source.appendChild(organization.toXml(doc))

