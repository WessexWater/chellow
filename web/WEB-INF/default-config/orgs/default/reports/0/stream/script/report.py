import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import net.sf.chellow.monad.vf.bo
import org.w3c.dom
import java.util

inv.getResponse().setContentType("image/svg+xml")


if inv.hasParameter("supply-id"):
	supplyId = inv.getMonadLong("supply-id")
	supply = net.sf.chellow.persistant08.Supply.getSupply(supplyId)
	data = net.sf.chellow.persistant08.Hiber.session().createQuery("from HhDatum datum where datum.channel.supply = :supply and datum.channel.isKwh is true order by datum.endDate").setEntity("supply", supply).setMaxResults(1440).list()
	supplyElement = supply.toXml(net.sf.chellow.monad.vf.bo.XMLTree("siteSupplies", net.sf.chellow.monad.vf.bo.XMLTree("site")).put("organization").put("source").put("generations", net.sf.chellow.monad.vf.bo.XMLTree("mpans", net.sf.chellow.monad.vf.bo.XMLTree("mpanCore").put("meterTimeswitch").put("hhdceChannels", net.sf.chellow.monad.vf.bo.XMLTree("contract", net.sf.chellow.monad.vf.bo.XMLTree("supplier"))).put("llf", net.sf.chellow.monad.vf.bo.XMLTree("voltageLevel").put("profileClass")))).put("mpanCores"), doc)
	source.appendChild(supplyElement)
	for datum in data:
		supplyElement.appendChild(datum.toXml(doc))
else:
	raise UserException.newInvalidParameter()