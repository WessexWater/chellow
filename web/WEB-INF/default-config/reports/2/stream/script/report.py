import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import net.sf.chellow.monad.vf.bo

if inv.hasParameter("site-id"):
	siteId = inv.getMonadLong("site-id")
	source.appendChild(organization.getSite(siteId).toXml(net.sf.chellow.monad.vf.bo.XMLTree("suppliesByStartDate",
				net.sf.chellow.monad.vf.bo.XMLTree("generationLast", net.sf.chellow.monad.vf.bo.XMLTree("mpans", net.sf.chellow.monad.vf.bo.XMLTree(
						"mpanCore"))).put("source")).put("organization"), doc))
else:
	raise UserException.newInvalidParameter()