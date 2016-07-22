def night_hv():
    return 1.012


def night_lv():
    return 1.042


def peak_hv():
    return 1.037


def peak_lv():
    return 1.104


def winter_weekday_hv():
    return 1.032


def winter_weekday_lv():
    return 1.095


def other_hv():
    return 1.029


def other_lv():
    return 1.070


def duos_day_hv_gbp_per_kwh():
    return 0.0008


def duos_night_hv_gbp_per_kwh():
    return 0.0004


def standing_hv_gbp_per_month():
    return 137.1792


def availability_hv_gbp_per_kva_per_month():
    return 1.3900


def reactive_hv_gbp_per_kvarh():
    return 0.0012


def duos_day_lv_gbp_per_kwh():
    return 0.0014


def duos_night_lv_gbp_per_kwh():
    return 0.0006


def standing_lv_gbp_per_month():
    return 51.4042


def availability_lv_gbp_per_kva_per_month():
    return 1.7307


def reactive_lv_gbp_per_kvarh():
    return 0.0024


def tariffs():
    return {
        '121': {
            'fixed-gbp-per-day': 1.6900,
            'availability-gbp-per-kva-per-day': 0.0569,
            'excess-availability-gbp-per-kva-per-day': 0.0569,
            'day-gbp-per-kwh': 0.0014,
            'night-gbp-per-kwh': 0.0006,
            'reactive-gbp-per-kvarh':  0.0024},
        '124': {
            'fixed-gbp-per-day': 1.6900,
            'availability-gbp-per-kva-per-day': 0.0569,
            'excess-availability-gbp-per-kva-per-day': 0.0569,
            'day-gbp-per-kwh': 0.0014,
            'night-gbp-per-kwh': 0.0006,
            'reactive-gbp-per-kvarh':  0.0024},
        '127': {
            'fixed-gbp-per-day': 1.6900,
            'availability-gbp-per-kva-per-day': 0.0569,
            'excess-availability-gbp-per-kva-per-day': 0.0569,
            'day-gbp-per-kwh': 0.0014,
            'night-gbp-per-kwh': 0.0006,
            'reactive-gbp-per-kvarh':  0.0024},
        '132': {
            'fixed-gbp-per-day': 1.6900,
            'availability-gbp-per-kva-per-day': 0.0569,
            'excess-availability-gbp-per-kva-per-day': 0.0569,
            'day-gbp-per-kwh': 0.0014,
            'night-gbp-per-kwh': 0.0006,
            'reactive-gbp-per-kvarh': 0.0024},
        '365': {
            'fixed-gbp-per-day': 4.5100,
            'availability-gbp-per-kva-per-day': 0.0457,
            'excess-availability-gbp-per-kva-per-day': 0.0457,
            'day-gbp-per-kwh': 0.0008,
            'night-gbp-per-kwh': 0.0004,
            'reactive-gbp-per-kvarh': 0.0012}}


def lafs():
    return {
        'lv': {
            'night': 1.042,
            'winter-weekday-peak': 1.104,
            'winter-weekday-day': 1.095,
            'other': 1.070},
        'hv': {
            'night': 1.012,
            'winter-weekday-peak': 1.037,
            'winter-weekday-day': 1.032,
            'other': 1.029}}
