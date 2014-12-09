from net.sf.chellow.monad import Monad
import db
import utils
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
User, Party, MarketRole = db.User, db.Party, db.MarketRole
UserException, form_str = utils.UserException, utils.form_str
Participant = db.Participant
render = templater.render
inv, template = globals()['inv'], globals()['template']


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
    sess = db.session()
    if inv.getRequest().getMethod() == 'POST':
        db.set_read_write(sess)
        email_address = inv.getString('email_address')
        password = form_str(inv, 'password')
        user_role_code = form_str(inv, 'user_role_code')
        role = db.UserRole.get_by_code(sess, user_role_code)
        try:
            party = None
            if role.code == 'party-viewer':
                party_id = inv.getLong('party_id')
                party = sess.query(Party).get(party_id)
            user = User.insert(
                sess, email_address, User.digest(password), role, party)
            sess.commit()
            inv.sendSeeOther('/reports/257/output/?user_id=' + str(user.id))
        except UserException, e:
            sess.rollback()
            render(inv, template, users_context(sess, message=str(e)), 400)
    else:
        render(inv, template, users_context(sess))
finally:
    if sess is not None:
        sess.close()
