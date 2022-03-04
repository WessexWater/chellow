from flask import g, render_template

import chellow.bill_importer


def test_status(mocker):
    batch = mocker.Mock()
    bill_import = chellow.bill_importer.BillImport(batch)
    bill_import.isAlive = mocker.Mock(return_value=True)
    bill_import.status()


def test_supplier_bill_import_html(mocker, app):
    with app.app_context():
        with app.test_request_context():
            g.user = None
            g.config = {}
            batch = mocker.Mock()
            failed_bills = [{"error": "MPAN not found"}]
            render_template(
                "/e/supplier_bill_import.html", batch=batch, failed_bills=failed_bills
            )
