import chellow.views
import chellow.utils


def test_make_val(mocker):
    v = {0, 'hello'}
    chellow.utils.make_val(v)
