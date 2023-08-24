from io import BytesIO
from utils import match


def test_edit_viewer_post(client, mocker):
    file_name = "sample.edi"
    file_bytes = "MHD=1+UTLHDR:3'".encode("utf8")
    f = BytesIO(file_bytes)

    data = {"edi_file": (f, file_name)}
    response = client.post("/edi_viewer", data=data)

    match(response, 200)
