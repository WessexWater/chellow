from java.lang import System
from net.sf.chellow.monad import Monad, Hiber
from sqlalchemy.orm import joinedload_all
import sys

Monad.getUtils()['imprt'](globals(), {
        'db': [
                'Contract', 'Party', 'User', 'set_read_write', 'session', 
                'UserRole'], 
        'utils': ['UserException'],
        'templater': ['render']})

def users_context(sess, message=None):
    users = sess.query(User).order_by(User.email_address).all()
    parties = sess.query(Party).from_statement("select party.* from party, " +
            "market_role, participant where party.market_role_id = market_role.id " +
            "and party.participant_id = participant.id order by " +
            "market_role.code, participant.code").all()
    fields = {'users': users, 'parties': parties, 'messages': None if message is None else [message]}
    user = inv.getUser()
    if user is not None:
        fields['current_user'] = user
    return fields

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'POST':
        set_read_write(sess)
        
        email_address = inv.getString('email_address')
        password = inv.getString('password')
        user_role_id = inv.getLong('user_role_id')
        role = UserRole.get_by_id(sess, user_role_id)
        try:
            party = None
            if role.code == 'party-viewer':
                party_id = inv.getLong('party_id')
                party = sess.query(Party).get(party_id)
            user = User.insert(sess, email_address, User.digest(password), role,
                    party)
            sess.commit()
            inv.sendSeeOther('/reports/257/output/?user_id=' + str(user.id))
        except UserException, e:
            sess.rollback()
            render(inv, template, users_context(sess, message=str(e)), 400)
    else:
        render(inv, template, users_context(sess))
finally:
    sess.close()