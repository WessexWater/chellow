from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
import sys

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
User, Party, MarketRole  = db.User, db.Party, db.MarketRole
Participant = db.Participant

def users_context(sess, message=None):
    users = sess.query(User).order_by(User.email_address).all()
    parties = sess.query(Party).join(MarketRole).join(Participant). \
        order_by(MarketRole.code, Participant.code).all()
    fields = {
        'users': users,
        'parties': parties,
        'messages': None if message is None else [message]}
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
