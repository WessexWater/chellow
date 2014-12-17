from net.sf.chellow.monad import Monad
import db
import utils
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Source, GeneratorType, GspGroup = db.Source, db.GeneratorType, db.GspGroup
Era, Supply = db.Era, db.Supply
UserException, form_date = utils.UserException, utils.form_date
render = templater.render
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, supply, message=None):
    messages = [] if message is None else [str(message)]
    sources = sess.query(Source).order_by(Source.code)
    generator_types = sess.query(GeneratorType).order_by(GeneratorType.code)
    gsp_groups = sess.query(GspGroup).order_by(GspGroup.code)
    eras = sess.query(Era).filter(
        Era.supply == supply).order_by(Era.start_date.desc())
    return {
        'supply': supply, 'messages': messages, 'sources': sources,
        'generator_types': generator_types, 'gsp_groups': gsp_groups,
        'eras': eras}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        supply_id = inv.getLong('supply_id')
        supply = Supply.get_by_id(sess, supply_id)
        render(inv, template, make_fields(sess, supply))
    else:
        db.set_read_write(sess)
        supply_id = inv.getLong('supply_id')
        supply = Supply.get_by_id(sess, supply_id)

        if inv.hasParameter("delete"):
            supply.delete(sess)
            sess.commit()
            inv.sendSeeOther("/reports/99/output/")
        elif inv.hasParameter("insert_era"):
            start_date = form_date(inv, 'start')
            supply.insert_era_at(sess, start_date)
            sess.commit()
            inv.sendSeeOther("/reports/7/output/?supply_id=" + str(supply.id))
        else:
            name = inv.getString("name")
            source_id = inv.getLong("source_id")
            gsp_group_id = inv.getLong("gsp_group_id")
            source = Source.get_by_id(sess, source_id)
            if source.code in ('gen', 'gen-net'):
                generator_type_id = inv.getLong("generator_type_id")
                generator_type = GeneratorType.get_by_id(
                    sess, generator_type_id)
            else:
                generator_type = None
            gsp_group = GspGroup.get_by_id(sess, gsp_group_id)
            supply.update(
                name, source, generator_type, gsp_group, supply.dno_contract)
            sess.commit()
            inv.sendSeeOther("/reports/7/output/?supply_id=" + str(supply.id))
except UserException, e:
    render(inv, template, make_fields(sess, supply, e), 400)
finally:
    if sess is not None:
        sess.close()
