import chellow.views
import chellow.utils


def test_make_val(mocker):
    v = {0, 'hello'}
    chellow.utils.make_val(v)


def test_PropDict(mocker):
    location = 'loc'
    props = {
        0: [{0: 1}]
    }
    chellow.utils.PropDict(location, props)
