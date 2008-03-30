import sys
import net.sf.chellow.billing
import net.sf.chellow.monad.ui
import net.sf.chellow.physical

def totalElement(account, startDate, finishDate):
    totalElement = net.sf.chellow.billing.BillElement("total", 103, "Dso cost")
    return totalElement