import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import calendar
import java.util
import net.sf.chellow.data08

for supply in net.sf.chellow.persistant08.Hiber.session().createQuery("from Supply supply").list():
    #source.appendChild(supply.getXML(doc))
    source.appendChild(supply.getXML(net.sf.chellow.monad.vf.bo.XMLTree("generationLast", net.sf.chellow.monad.vf.bo.XMLTree("mpans", net.sf.chellow.monad.vf.bo.XMLTree("lineLossFactor", net.sf.chellow.monad.vf.bo.XMLTree("voltageLevel")))).put("siteSupplies", net.sf.chellow.monad.vf.bo.XMLTree("site")), doc))
