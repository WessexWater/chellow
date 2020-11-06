import re


def match(response, status_code, *patterns):
    response_str = response.get_data(as_text=True)

    assert response.status_code == status_code, response_str

    for regex in patterns:
        assert re.search(
            regex, response_str, flags=re.MULTILINE + re.DOTALL), response_str
