from net.sf.chellow.physical import HhStartDate

def hh(bill, supply_source, rate, differentiator, whole_data=None):
    if whole_data is None:
        whole_data = supply_source.whole_data

    hh_data = whole_data['data']
    summary = whole_data['summary']

    bill['fit-' + differentiator + '-msp-kwh'] = summary['sum-msp-kwh']
    bill['fit-' + differentiator + '-rate'] = rate
    bill['fit-' + differentiator + '-gbp'] = summary['sum-msp-kwh'] * rate