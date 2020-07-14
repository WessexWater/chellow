import chellow.bill_importer


def test_status(mocker):
    batch = mocker.Mock()
    bill_import = chellow.bill_importer.BillImport(batch)
    bill_import.isAlive = mocker.Mock(return_value=True)
    bill_import.status()
