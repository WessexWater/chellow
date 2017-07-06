from collections import defaultdict
from werkzeug.exceptions import BadRequest


def make_create_future_func_simple(contract_name, fnames=None):
    def create_future_func_simple(multiplier, constant):
        mult = float(multiplier)
        const = float(constant)
        if fnames is None:
            def future_func(ns):
                new_ns = {}
                for k, v in ns.items():
                    new_ns[k] = float(v) * mult + const

                return new_ns
        else:
            def future_func(ns):
                new_ns = {}
                for fname in fnames:
                    try:
                        new_ns[fname] = ns[fname] * mult + const
                    except KeyError:
                        raise BadRequest(
                            "Can't find " + fname + " in rate script " +
                            str(ns) + " for contract name " + contract_name +
                            " .")

                return new_ns
        return future_func
    return create_future_func_simple


def make_create_future_func_monthly(contract_name, fnames):
    def create_future_func_monthly(multiplier, constant):

        def future_func(ns):
            new_ns = {}
            for fname in fnames:
                old_result = ns[fname]
                last_value = old_result[sorted(old_result.keys())[-1]]
                new_ns[fname] = defaultdict(
                    lambda: last_value, [
                        (k, v * multiplier + constant)
                        for k, v in old_result.items()])

            return new_ns
        return future_func
    return create_future_func_monthly
