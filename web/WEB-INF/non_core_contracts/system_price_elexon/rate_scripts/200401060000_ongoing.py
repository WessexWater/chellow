def ssp_future_func(historical_ssps):
    return dict((k, v * 1) for k, v in historical_ssps.items())

def ssps():
    return ssp_future_func

def sbp_future_func(historical_sbps):
    return dict((k, v * 1) for k, v in historical_sbps.items())

def sbps():
    return sbp_future_func