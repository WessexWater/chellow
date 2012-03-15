class UserException(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = 'Something went wrong with Foo.'
        super(UserException, self).__init__(msg)
