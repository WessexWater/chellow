import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import calendar
import java.util
import net.sf.chellow.data08

#intent: take a list of sites (begin with one) for a given date (default of the #current day) output the data for 24 hours in meniscus friendly form (MPAN ; #date/time ; value) as a semicolon seperated .txt file

#siteID.getString() [how to extract a string from a monad string]
#date.getDate() [how to extract a date from a monad date]

#Find site ID, or default if no site passed in (eg script is being called stand #alone
if inv.hasParameter("site-id"):
     siteID = inv.getMonadString("site-id")
else:
     siteID = "No Site Specified"

#Provide the current date to use if no parameters have been passed
currentDate = net.sf.chellow.monad.vf.bo.MonadDate()

if inv.hasParameter("start-year"):
     date = inv.getMonadDate("start")
else:
     date = currentDate.getDate()


source.appendChild(siteID)
#source.appendChild(date.toXML(doc))