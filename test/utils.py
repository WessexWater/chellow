import re
from time import sleep


def match(response, status_code, *patterns):
    response_str = response.get_data(as_text=True)

    assert response.status_code == status_code, response_str

    for regex in patterns:
        assert re.search(
            regex, response_str, flags=re.MULTILINE + re.DOTALL
        ), response_str


def match_tables(expected_table, actual_table):
    len_expected_table = len(expected_table)
    len_actual_table = len(actual_table)
    assert len_expected_table == len_actual_table, (
        f"The length of the expected table {len_expected_table} does not match the "
        f"lngth of the actual table {len_actual_table}"
    )
    for i, (expected_row, actual_row) in enumerate(zip(expected_table, actual_table)):
        len_expected_row, len_actual_row = len(expected_row), len(actual_row)
        assert len_expected_row == len_actual_row, (
            f"For row {i} the length {len_expected_row} of the expected row does not "
            f"match the lngth of the actual row {len_actual_row}\n"
            f"{expected_row}\n"
            f"{actual_row}\n"
        )
        for j, (expected_val, actual_val) in enumerate(zip(expected_row, actual_row)):
            assert (
                expected_val == actual_val
            ), f"On row {i} column {j}, {expected_val} != {actual_val}"


def match_repeat(client, path, match, seconds=5):
    for second in range(seconds):
        response = client.get(path)
        response_str = response.get_data(as_text=True)
        if match in response_str:
            return response
        elif second == seconds - 1:
            assert match in response_str, response_str
        else:
            sleep(1)
