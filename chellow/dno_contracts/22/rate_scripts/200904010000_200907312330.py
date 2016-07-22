def lafs():
    return {
        'hv': {
            'winter-weekday-peak': 1.058,
            'winter-weekday-day': 1.051,
            'night': 1.041,
            'other': 1.046},
        'lv-sub': {
            'winter-weekday-peak': 1.070,
            'winter-weekday-day': 1.066,
            'night': 1.060,
            'other': 1.062},
        'lv-net': {
            'winter-weekday-peak': 1.079,
            'winter-weekday-day': 1.073,
            'night': 1.067,
            'other': 1.069}}


def winter_weekday_peak_hv():
    return 1.058


def winter_weekday_day_hv():
    return 1.051


def night_hv():
    return 1.041


def other_hv():
    return 1.046


def winter_weekday_peak_lv_sub():
    return 1.070


def winter_weekday_day_lv_sub():
    return 1.066


def night_lv_sub():
    return 1.060


def other_lv_sub():
    return 1.062


def winter_weekday_peak_lv_net():
    return 1.079


def winter_weekday_day_lv_net():
    return 1.073


def night_lv_net():
    return 1.067


def other_lv_net():
    return 1.069


def duos_day_hv_gbp_per_kwh():
    return 0.0047


def duos_night_hv_gbp_per_kwh():
    return 0.0014


def standing_hv_gbp_per_month():
    return 0


def availability_hv_gbp_per_kva_per_day():
    return 0.0387


def duos_reactive_hv_gbp_per_kvarh():
    return 0.0023


def duos_day_lv_net_gbp_per_kwh():
    return 0.0127


def duos_night_lv_net_gbp_per_kwh():
    return 0.0045


def standing_lv_net_gbp_per_month():
    return 0


def availability_lv_net_gbp_per_kva_per_day():
    return 0.039


def duos_reactive_lv_net_gbp_per_kvarh():
    return 0.0042


def duos_day_lv_sub_gbp_per_kwh():
    return 0.0081


def duos_night_lv_sub_gbp_per_kwh():
    return 0.0028


def standing_lv_sub_gbp_per_month():
    return 0


def availability_lv_sub_gbp_per_kva_per_day():
    return 0.0389


def duos_reactive_lv_sub_gbp_per_kvarh():
    return 0.0033


def tariffs():
    return {
        '510': {
            'gbp-per-kva-per-day': 0.038700,
            'day-gbp-per-kwh': 0.004700,
            'night-gbp-per-kwh': 0.001400,
            'reactive-gbp-per-kvarh': 0.002300},
        '520': {
            'gbp-per-kva-per-day': 0.038700,
            'day-gbp-per-kwh': 0.004700,
            'night-gbp-per-kwh': 0.001400,
            'reactive-gbp-per-kvarh': 0.002300},
        '540': {
            'gbp-per-kva-per-day': 0.038900,
            'day-gbp-per-kwh': 0.008100,
            'night-gbp-per-kwh': 0.002800,
            'reactive-gbp-per-kvarh': 0.003300},
        '550': {
            'gbp-per-kva-per-day': 0.038900,
            'day-gbp-per-kwh': 0.008100,
            'night-gbp-per-kwh': 0.002800,
            'reactive-gbp-per-kvarh': 0.003300},
        '570': {
            'gbp-per-kva-per-day': 0.039000,
            'day-gbp-per-kwh': 0.012700,
            'night-gbp-per-kwh': 0.004500,
            'reactive-gbp-per-kvarh': 0.004200},
        '580': {
            'gbp-per-kva-per-day': 0.039000,
            'day-gbp-per-kwh': 0.012700,
            'night-gbp-per-kwh': 0.004500,
            'reactive-gbp-per-kvarh': 0.004200}}
