from net.sf.chellow.monad import Monad
import utils
Monad.getUtils()['impt'](globals(), 'utils')
inv = globals()['inv']


def content():
    yield '''
@import url(https://fonts.googleapis.com/css?family=Overclock);
table {
    border: thin solid gray;
    border-collapse: collapse;
}

td {
    border: thin solid gray;
    padding-left: 0.2em;
    padding-right: 0.2em;
}
th {
    border: thin solid gray;
}
#title {
    font-size: xx-large;
}
.logo {
    color: green;
}


body {
    line-height: 1.2;
    font-size: 0.9em;
    font-family: 'Overclock', sans-serif;
    background-color: rgb(255, 236, 139);
}
'''
utils.send_response(inv, content, 200, mimetype='text/css')
