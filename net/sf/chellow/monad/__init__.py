from chellow import app

def impt(gbls, *lib_names):
    libs = app.config['libs']
    for lib_name in lib_names:
        try:
            gbls[lib_name] = libs[lib_name]
        except KeyError:
            raise UserException(
                "Can't find a library called " + str(lib_name))

IMPT =  {'impt': impt}

class Monad():

    @staticmethod
    def getUtils():
        return IMPT
