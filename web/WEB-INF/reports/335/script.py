from net.sf.chellow.monad import Monad
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
inv, template = globals()['inv'], globals()['template']

templater.render(inv, template, {})
