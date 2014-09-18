from net.sf.chellow.monad import Hiber, UserException, Monad
import os

name = inv.getString("name")
head, name = os.path.split(os.path.normcase(os.path.normpath(name)))

download_path = Monad.getContext().getRealPath("/downloads")

method = inv.getRequest().getMethod()

if method == 'GET':
    fl = open(os.path.join(download_path, name))

    inv.getResponse().setContentType("text/csv")
    inv.getResponse().setHeader('Content-Disposition', 'attachment; filename="' + name + '"')

    pw = inv.getResponse().getWriter()
    for line in fl:
        pw.print(line)

    pw.close()
    fl.close()
elif method == 'POST':
    os.remove(name)
    inv.sendSeeOther("/reports/251/output/")
else:
    raise UserException("Don't recognize the method: " + method)