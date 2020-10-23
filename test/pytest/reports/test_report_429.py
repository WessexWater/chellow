from chellow.utils import utc_datetime
import chellow.reports.report_429


def test_process_g_bill_ids(mocker):
    sess = mocker.Mock()
    forecast_date = utc_datetime(2010, 4, 1)

    query = mocker.Mock()
    sess.query.return_value = query
    m_filter = mocker.Mock()
    query.filter.return_value = m_filter
    g_bill = mocker.Mock()
    m_filter.one.return_value = g_bill
    g_bill.g_reads = []

    m_filter.order_by.return_value = []

    g_bill.g_supply = mocker.Mock()
    g_bill.start_date = forecast_date
    g_bill.finish_date = forecast_date

    MockGBill = mocker.patch('chellow.reports.report_429.GBill', autospec=True)
    MockGBill.g_supply = mocker.Mock()
    MockGBill.start_date = forecast_date
    MockGBill.finish_date = forecast_date

    find_g_era_at = g_bill.g_supply.find_g_era_at

    report_context = {}
    g_bill_ids = [1]
    bill_titles = []
    vbf = mocker.Mock()
    titles = []
    csv_writer = mocker.Mock()

    chellow.reports.report_429._process_g_bill_ids(
        sess, report_context, g_bill_ids, forecast_date, bill_titles, vbf,
        titles, csv_writer)

    find_g_era_at.assert_not_called()
