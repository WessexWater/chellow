def future_func(historical_rcrcs):
    return dict((k, v * 1.032) for k, v in historical_rcrcs.items())

def rates():
    return future_func