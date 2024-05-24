from flask import g, render_template

from chellow.e.bill_importer import BillImport, find_parser_names


def test_status(mocker):
    batch = mocker.Mock()
    bill_import = BillImport(batch)
    bill_import.isAlive = mocker.Mock(return_value=True)
    bill_import.status()


def test_supplier_bill_import_html(mocker, app):
    with app.app_context():
        with app.test_request_context():
            g.user = None
            g.config = {}
            batch = mocker.Mock()
            failed_bills = [{"error": "MPAN not found"}]
            failed_max_registers = 0
            render_template(
                "/e/supplier_bill_import.html",
                batch=batch,
                failed_bills=failed_bills,
                failed_max_registers=failed_max_registers,
            )


def test_find_parser_names():
    assert len(find_parser_names()) > 0
