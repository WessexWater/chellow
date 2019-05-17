import chellow.views
from werkzeug.exceptions import BadRequest
from sqlalchemy.orm.session import Session
from chellow.utils import utc_datetime


def test_supply_edit_post(mocker):
    """ When inserting an era that fails, make sure rollback is called.
    """
    supply_id = 1
    g = mocker.patch("chellow.views.g", autospec=True)
    g.sess = mocker.Mock(spec=Session)
    supply_class = mocker.patch("chellow.views.Supply", autospec=True)

    request = mocker.patch("chellow.views.request", autospec=True)
    request.form = {'insert_era': 0}

    req_date = mocker.patch("chellow.views.req_date", autospec=True)
    req_date.return_value = utc_datetime(2019, 1, 1)

    mocker.patch("chellow.views.flash", autospec=True)
    era_class = mocker.patch("chellow.views.Era", autospec=True)
    era_class.supply = mocker.Mock()

    mocker.patch("chellow.views.make_response", autospec=True)
    mocker.patch("chellow.views.render_template", autospec=True)

    supply = mocker.Mock()
    supply.insert_era_at.side_effect = BadRequest()

    supply_class.get_by_id.return_value = supply

    chellow.views.supply_edit_post(supply_id)
    g.sess.rollback.assert_called_once_with()
