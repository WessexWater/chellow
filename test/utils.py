import re
from itertools import zip_longest


def match(response, status_code, *patterns):
    response_str = response.get_data(as_text=True)

    assert response.status_code == status_code, response_str

    for regex in patterns:
        assert re.search(
            regex, response_str, flags=re.MULTILINE + re.DOTALL
        ), response_str


def match_tables(table_1, table_2):
    for r1, r2 in zip_longest(table_1, table_2):
        for c1, c2 in zip_longest(r1, r2):
            if c1 != c2:
                raise Exception(f"Two cells don't match: {c1} and {c2}")

    assert table_1 == table_2
