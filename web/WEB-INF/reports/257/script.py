from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
UserException = utils.UserException
render = templater.render
User, Party = db.User, db.Party

def user_fields(sess, user, message=None):
    parties = sess.query(Party).from_statement("""select party.* from party,
        market_role, participant where party.market_role_id = market_role.id
        and party.participant_id = participant.id order by market_role.code, 
        participant.code""").all()
    return {'user': user, 'parties': parties,
            'messages': None if message is None else [message]}


sess = None
try:
    sess = db.session()

    if inv.getRequest().getMethod() == 'GET':
        user_id = inv.getInteger('user_id')
        user = User.get_by_id(sess, user_id)
        from chellow import app
        render(inv, template, user_fields(sess, user))
    else:
        db.set_read_write(sess)
        user_id = inv.getInteger('user_id')
        user = User.get_by_id(sess, user_id)
        if inv.hasParameter('delete'):
            sess.delete(user)
            sess.commit()
            inv.sendSeeOther('/reports/255/output/?user_id=' + str(user.id))
        elif inv.hasParameter('current_password'):
            current_password = inv.getString('current_password')
            new_password = inv.getString('new_password')
            confirm_new_password = inv.getString('confirm_new_password')
            if user.password_digest != User.digest(current_password):
                raise UserException("The current password is incorrect.")
            if new_password != confirm_new_password:
                raise UserException("The new passwords aren't the same.")
            if len(new_password) < 6:
                raise UserException("The password must be at least 6 " +
                        "characters long.")
            user.password_digest = User.digest(new_password)
            sess.commit()
            inv.sendSeeOther('/reports/255/output/?user_id=' + str(user.id))
        else:
            email_address = inv.getString('email_address')
            role_id = inv.getInteger('user_role_id')
            role = db.UserRole.get_by_id(sess, role_id)
            party = None
            if role.code == 'party-viewer':
                party_id = inv.getInteger('party_id')
                party = Party.get_by_id(sess, party_id)
            user.update(email_address, role, party)
            sess.commit()
            inv.sendSeeOther('/reports/255/output/?user_id=' + str(user.id))
except UserException, e:
    render(inv, template, user_fields(sess, user, str(e)))
finally:
    if sess is not None:
        sess.close()
