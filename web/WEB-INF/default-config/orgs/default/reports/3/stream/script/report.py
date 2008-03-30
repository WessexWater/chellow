import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import net.sf.chellow.monad.vf.bo
import org.w3c.dom

if inv.hasParameter("supply-id"):
	supplyId = inv.getMonadLong("supply-id")
	source.appendChild(net.sf.chellow.persistant08.Supply.getSupply(supplyId).getXML(net.sf.chellow.monad.vf.bo.XMLTree("siteSupplies",
				net.sf.chellow.monad.vf.bo.XMLTree("site")).put("organization").put("source").put(
				"generations",
				net.sf.chellow.monad.vf.bo.XMLTree("mpans", net.sf.chellow.monad.vf.bo.XMLTree("mpanCore").put("meterTimeswitch").put("hhdceChannels", net.sf.chellow.monad.vf.bo.XMLTree("contract", net.sf.chellow.monad.vf.bo.XMLTree("supplier"))).put(
						"lineLossFactor", net.sf.chellow.monad.vf.bo.XMLTree("voltageLevel").put("profileClass")))).put(
				"mpanCores"), doc))
else:
	raise UserException.newInvalidParameter()