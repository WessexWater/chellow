from decimal import Decimal
from io import BytesIO
from time import sleep

from flask import g

from sqlalchemy import text

from utils import match

import chellow.gas.bill_import
from chellow.models import (
    BillType,
    GContract,
    GDn,
    GReadType,
    GReadingFrequency,
    GUnit,
    Site,
    insert_bill_types,
    insert_g_read_types,
    insert_g_reading_frequencies,
    insert_g_units,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_batch_get_empty(client, sess):
    g_contract = GContract.insert_supplier(
        sess, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    sess.commit()

    response = client.get(f"/g/batches/{g_batch.id}")

    match(response, 200)


def test_batch_get(client, sess):
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")

    g_ldz = g_dn.insert_g_ldz(sess, "EA")

    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")

    insert_g_units(sess)

    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    insert_g_reading_frequencies(sess)

    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    g_supply = site.insert_g_supply(
        sess,
        "87614362",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    breakdown = {"units_consumed": 771}

    insert_bill_types(sess)

    bill_type_n = BillType.get_by_code(sess, "N")

    g_batch.insert_g_bill(
        sess,
        g_supply,
        bill_type_n,
        "55h883",
        "dhgh883",
        utc_datetime(2019, 4, 3),
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31, 23, 30),
        Decimal("45"),
        Decimal("12.40"),
        Decimal("1.20"),
        Decimal("14.52"),
        "",
        breakdown,
    )

    sess.commit()

    response = client.get(f"/g/batches/{g_batch.id}")

    match(response, 200)


def test_batch_add_get(client, sess):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, valid_from, None, {}
    )

    batch_reference = "b1"
    batch_description = "Jan batch"
    g_contract.insert_g_batch(sess, batch_reference, batch_description)

    sess.commit()

    response = client.get(f"/g/supplier_contracts/{g_contract.id}/add_batch")

    match(response, 200, rf"{batch_reference}", rf"{batch_description}")


def test_batch_edit_post(sess, client):
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    mprn = "750278673"
    site.insert_g_supply(
        sess,
        mprn,
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )
    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")
    sess.commit()

    data = {
        "update": "Update",
        "reference": "b2",
        "description": "Feb batch",
    }

    response = client.post(f"/g/batches/{g_batch.id}/edit", data=data)

    match(response, 303, rf"/g/batches/{g_batch.id}")


def test_batch_edit_delete(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    g_contract = GContract.insert(sess, False, "Fusion 2020", "", {}, vf, None, {})
    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")
    sess.commit()

    response = client.delete(f"/g/batches/{g_batch.id}/edit")

    match(response, 200)

    assert response.headers["HX-Redirect"].endswith(
        f"/g/batches?g_contract_id={g_contract.id}"
    )


def test_batch_csv_get(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    g_contract = GContract.insert(sess, False, "Fusion 2020", "", {}, vf, None, {})
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    mprn = "750278673"
    g_supply = site.insert_g_supply(
        sess,
        mprn,
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )
    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")
    breakdown = {"units_consumed": 771}

    insert_bill_types(sess)

    bill_type_n = BillType.get_by_code(sess, "N")

    g_bill = g_batch.insert_g_bill(
        sess,
        g_supply,
        bill_type_n,
        "55h883",
        "dhgh883",
        utc_datetime(2019, 4, 3),
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31, 23, 30),
        Decimal("45"),
        Decimal("12.40"),
        Decimal("1.20"),
        Decimal("14.52"),
        "",
        breakdown,
    )
    insert_g_read_types(sess)

    g_read_type_A = GReadType.get_by_code(sess, "A")

    g_bill.insert_g_read(
        sess,
        "ghu5438gt",
        g_unit_M3,
        1,
        37,
        Decimal(800),
        utc_datetime(2020, 1, 1),
        g_read_type_A,
        Decimal(900),
        utc_datetime(2020, 1, 31),
        g_read_type_A,
    )
    sess.commit()

    response = client.get(f"/g/batches/{g_batch.id}/csv")
    match(response, 200)

    lines = [
        [
            "Contract",
            "Batch Reference",
            "Bill Reference",
            "Account",
            "Issued",
            "From",
            "To",
            "kWh",
            "Net",
            "VAT",
            "Gross",
            "Type",
            "breakdown",
            "0_msn",
            "0_unit",
            "0_correction_factor",
            "0_calorific_value",
            "0_prev_date",
            "0_prev_value",
            "0_prev_type",
            "0_pres_date",
            "0_pres_value",
            "0_pres_type",
        ],
        [
            "Fusion 2020",
            "b1",
            "55h883",
            "dhgh883",
            "2019-04-03 01:00",
            "2020-01-01 00:00",
            "2020-01-31 23:30",
            "45",
            "12.40",
            "1.20",
            "14.52",
            "N",
            '"{\n  ""units_consumed"": 771,\n}"',
            "ghu5438gt",
            "M3",
            "1",
            "37",
            "2020-01-01 00:00",
            "800",
            "A",
            "2020-01-31 00:00",
            "900",
            "A",
        ],
    ]
    pattern = "\r\n".join(",".join(line) for line in lines) + "\r\n"
    actual = response.get_data(as_text=True)
    assert pattern == actual


def test_bill_get(client, sess):
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")

    g_ldz = g_dn.insert_g_ldz(sess, "EA")

    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")

    insert_g_units(sess)

    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    insert_g_reading_frequencies(sess)

    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    g_supply = site.insert_g_supply(
        sess,
        "87614362",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    breakdown = {"units_consumed": 771}

    insert_bill_types(sess)

    bill_type_n = BillType.get_by_code(sess, "N")

    g_bill = g_batch.insert_g_bill(
        sess,
        g_supply,
        bill_type_n,
        "55h883",
        "dhgh883",
        utc_datetime(2019, 4, 3),
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31, 23, 30),
        Decimal("45"),
        Decimal("12.40"),
        Decimal("1.20"),
        Decimal("14.52"),
        "",
        breakdown,
    )

    sess.commit()

    response = client.get(f"/g/bills/{g_bill.id}")

    match(response, 200, r"<tr>\s*", r"<td>units</td>\s*", r"<td>771</td>")


def test_bill_add_post(sess, client):
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    mprn = "750278673"
    site.insert_g_supply(
        sess,
        mprn,
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )
    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")
    insert_bill_types(sess)
    sess.commit()

    data = {
        "bill_type_id": "2",
        "mprn": mprn,
        "reference": "765988",
        "account": "1",
        "issue_year": "2017",
        "issue_month": "02",
        "issue_day": "03",
        "issue_hour": "00",
        "issue_minute": "00",
        "start_year": "2017",
        "start_month": "03",
        "start_day": "01",
        "start_hour": "00",
        "start_minute": "00",
        "finish_year": "2017",
        "finish_month": "04",
        "finish_day": "01",
        "finish_hour": "00",
        "finish_minute": "30",
        "kwh": "0.00",
        "net": "0.00",
        "vat": "0.00",
        "gross": "0.00",
        "breakdown": "{}",
    }

    response = client.post(f"/g/batches/{g_batch.id}/add_bill", data=data)

    match(response, 303, r"/g/bills/1")


def test_bill_edit_post(sess, client):
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    g_supply = site.insert_g_supply(
        sess,
        "87614362",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )
    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    breakdown = {"units_consumed": 771}
    insert_bill_types(sess)
    bill_type_n = BillType.get_by_code(sess, "N")
    g_bill = g_batch.insert_g_bill(
        sess,
        g_supply,
        bill_type_n,
        "55h883",
        "dhgh883",
        utc_datetime(2019, 4, 3),
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31, 23, 30),
        Decimal("45"),
        Decimal("12.40"),
        Decimal("1.20"),
        Decimal("14.52"),
        "",
        breakdown,
    )

    sess.commit()

    data = {
        "bill_type_id": "3",
        "reference": "8899900012",
        "account": "college_rooms",
        "issue_year": "2015",
        "issue_month": "11",
        "issue_day": "01",
        "issue_hour": "00",
        "issue_minute": "00",
        "start_year": "2015",
        "start_month": "09",
        "start_day": "01",
        "start_hour": "01",
        "start_minute": "00",
        "finish_year": "2015",
        "finish_month": "09",
        "finish_day": "30",
        "finish_hour": "01",
        "finish_minute": "00",
        "kwh": "4500901",
        "net_gbp": "6972.33",
        "vat_gbp": "1003.89",
        "gross_gbp": "7976.22",
        "raw_lines": "reference,mprn,bill_type,account,issue_date,"
        "start_date,finish_date,kwh,net_gbp,vat_gbp,gross_gbp,"
        "breakdown,msn,unit,correction_factor,"
        "calorific_value,prev_date,prev_value,prev_type,pres_date,"
        "prev_value,pres_type\n"
        "8899900012,750278673,N,college_rooms,2015-11-01 00:00,"
        "2015-09-01 00:00,2015-09-30 00:00,4500901,6972.33,1003.89,"
        '7976.22,{"gas_rate": 0.019448, "gas_gbp": 8936.13,'
        '"ccl_gbp": 275.32, "vat_0500pc": 0.3, "vat_1500pc": 49.12, '
        '"vat_1750pc": 55.7, "vat_2000pc": 801},hwo8tt,HCUF,FALSE,,'
        "39.300811,2015-09-01 00:00,567822,A,2015-10-01 00:00,"
        "575652,A",
        "breakdown": '{"ccl_gbp": 275.32, "gas_gbp": 8936.13, '
        '"gas_rate": 0.019448, "vat_0500pc": 0.3, "vat_1500pc": 49.12,'
        '"vat_1750pc": 55.7, "vat_2000pc": 801}',
    }

    response = client.post(f"/g/bills/{g_bill.id}/edit", data=data)

    match(response, 303, rf"/g/bills/{g_bill.id}")


def test_bill_imports_post_full(mocker, app, client, sess):
    file_lines = (
        "STX=ANA:1+Marsh Gas:MARSH Gas Limited+BPAJA:Bill Paja 771+"
        "171023:867369+856123++UTLHDR'",
        "MHD=1+UTLHDR:3'",
        "TYP=0715'",
        "SDT=Marsh Gas+Marsh Gas Limited++818671845'",
        "CDT=BPAJA:BPAJA+Bill Paja Limited - BPAJA++1'",
        "FIL=1+1+171023'",
        "MTR=6'",
        "MHD=2+UTLBIL:3'",
        "CLO=::10205041+Bill Paja Limited+Mole Hall, BATH::BA1 9MH'",
        "BCD=171022+171022+7868273476++M+N++170601:170630'",
        "CCD=1+1::GAS+MARSH6:Meter Reading++hyygk4882+87614362+170701+170601++"
        "83551:01:81773:01+8746000+771000:M3+CF:102264+841349:M3++831200:KWH+"
        "170601+170701'",
        "ADJ=1+1+CV:3930000'",
        "CCD=2+3::PPK+MARSH6:Unidentified Gas++++++++8746000++CF:100000++"
        "008521+8746000+170601+170631+008727+091'",
        "CCD=3+3::PPK+MARSH6:Commodity++++++++8746000++CF:100000++9873510+"
        "8746000+170601+170630+815510+9931'",
        "CCD=4+3::PPD+MARSH6:Transportation++++++++30000++CF:100000++86221004+"
        "30000+170601+170630+86221004+9224'",
        "CCD=5+3::PPD+MARSH6:Meter Reading++++++++30000++CF:100000++82113473+"
        "30000+170601+170630+8582284+941'",
        "CCD=6+3::PPD+MARSH6:Meter Rental++++++++30000++CF:100000++3228000+"
        "30000+170601+170630+8993000+841'",
        "CCD=7+3::PPK+MARSH6:Transportation++++++++8116500++CF:100000++"
        "005337+4617800+170601+170630+006120+882'",
        "VAT=1+++L+7986+23885+331+86334'",
        "BTL=000+88772+332++77345'",
        "MTR=14'",
        "MHD=2+UTLBIL:3'",
        "CLO=::10205041+Bill Paja Limited+Mole Hall, BATH::BA1 9MH'",
        "BCD=171022+171022+7868273476++M+N++170601:170630'",
        "CCD=1+1::GAS+MARSH6:Meter Reading++hyygk4882+87614362+170701+170601++"
        "83551:01:81773:01+8746000+771000:M3+CF:102264+841349:M3++831200:KWH+"
        "170601+170701'",
        "ADJ=1+1+CV:3930000'",
        "CCD=2+3::PPK+MARSH6:Unidentified Gas++++++++8746000++CF:100000++"
        "008521+8746000+170601+170631+008727+091'",
        "CCD=3+3::PPK+MARSH6:Commodity++++++++8746000++CF:100000++9873510+"
        "8746000+170601+170630+815510'",
        "CCD=4+3::PPD+MARSH6:Transportation++++++++30000++CF:100000++86221004+"
        "30000+170601+170630+86221004+9224'",
        "CCD=5+3::PPD+MARSH6:Meter Reading++++++++30000++CF:100000++82113473+"
        "30000+170601+170630+8582284+941'",
        "CCD=6+3::PPD+MARSH6:Meter Rental++++++++30000++CF:100000++3228000+"
        "30000+170601+170630+8993000+841'",
        "CCD=7+3::PPK+MARSH6:Transportation++++++++8116500++CF:100000++005337+"
        "4617800+170601+170630+006120+882'",
        "VAT=1+++L+7986+23885+331+86334'",
        "BTL=000+88772+332++77345'",
        "MTR=14'",
        "END=288'",
    )

    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")

    g_ldz = g_dn.insert_g_ldz(sess, "EA")

    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")

    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    insert_bill_types(sess)

    insert_g_units(sess)

    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    insert_g_reading_frequencies(sess)

    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    site.insert_g_supply(
        sess,
        "87614362",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    insert_g_read_types(sess)

    sess.commit()

    file_name = "gas.engie.edi"

    file_bytes = "\n".join(file_lines).encode("utf8")

    f = BytesIO(file_bytes)

    data = {
        "g_batch_id": str(g_batch.id),
        "import_file": (f, file_name),
        "parser_name": "engie_edi",
    }

    response = client.post("/g/bill_imports", data=data)

    match(response, 303, "/g/bill_imports/0")

    importer = next(iter(chellow.gas.bill_import.importers.values()))

    for _ in range(5):
        if importer.is_alive():
            sleep(1)
        else:
            break

    response = client.get("/g/bill_imports/0")

    match(
        response,
        200,
        r"All the bills have been successfully loaded and attached to the batch.",
        r"<td>M3</td>",
    )

    sess.rollback()

    res = sess.execute(text("select breakdown from g_bill where id = 2"))

    assert '"units_consumed": 771,' in next(res)[0]


def test_bill_imports_post(mocker, app, client, sess):
    g_contract = GContract.insert(
        sess,
        False,
        "Fusion 2020",
        "",
        {},
        utc_datetime(2019, 1, 1),
        utc_datetime(2019, 2, 28, 23, 30),
        {},
    )

    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    sess.commit()

    file_name = "gas.engie.edi"

    file_bytes = b"edifile'"

    f = BytesIO(file_bytes)

    parser_name = "engie_edi"
    data = {
        "g_batch_id": str(g_batch.id),
        "import_file": (f, file_name),
        "parser_name": parser_name,
    }

    import_id = 3

    mock_start_importer = mocker.patch(
        "chellow.gas.views.chellow.gas.bill_import.start_bill_importer",
        return_value=import_id,
    )

    response = client.post("/g/bill_imports", data=data)

    mock_start_importer.assert_called_with(
        g.sess, g_batch.id, file_name, file_bytes, parser_name
    )

    match(response, 303, "/g/bill_imports/3")


def test_batch_add_post(client, sess):
    g_contract = GContract.insert_supplier(
        sess,
        "Fusion 2020",
        "",
        {},
        utc_datetime(2019, 1, 1),
        utc_datetime(2019, 2, 28, 23, 30),
        {},
    )

    sess.commit()

    data = {"reference": "engie_edi", "description": "Engie EDI"}

    response = client.post(
        f"/g/supplier_contracts/{g_contract.id}/add_batch", data=data
    )

    match(response, 303, "/g/batches/1")


def test_industry_contracts(client, sess):
    contract = GContract.insert_industry(
        sess,
        "Fusion 2020",
        "",
        {},
        utc_datetime(2019, 1, 1),
        None,
        {},
    )
    contract.insert_g_rate_script(sess, utc_datetime(2019, 2, 1), {})
    sess.commit()

    response = client.get("/g/industry_contracts")

    match(response, 200, r"<td>\s*2019-01-01 00:00\s*</td>\s*<td>\s*Ongoing\s*</td>")


def test_industry_contract_edit_patch(client, sess):
    contract = GContract.insert_industry(
        sess,
        "Fusion 2020",
        "",
        {},
        utc_datetime(2019, 1, 1),
        None,
        {},
    )
    sess.commit()

    data = {
        "name": "Fusion 2020",
        "charge_script": "",
        "properties": "{}",
        "state": '{"hinderance": "sloth"}',
    }
    response = client.patch(f"/g/industry_contracts/{contract.id}/edit", data=data)
    match(response, 303)
    response = client.get(f"/g/industry_contracts/{contract.id}")
    match(response, 200, "&#34;hinderance&#34;: &#34;sloth&#34;")


def test_supplier_contracts(client, sess):
    GContract.insert_supplier(
        sess,
        "Fusion 2020",
        "",
        {},
        utc_datetime(2019, 1, 1),
        utc_datetime(2019, 2, 28, 23, 30),
        {},
    )

    sess.commit()
    response = client.get("/g/supplier_contracts")

    match(response, 200)


def test_supplier_contracts_empty(client, sess):
    response = client.get("/g/supplier_contracts")

    match(response, 200)


def test_supplier_contract_edit_delete(client, sess):
    contract = GContract.insert_supplier(
        sess,
        "Fusion 2020",
        "",
        {},
        utc_datetime(2019, 1, 1),
        None,
        {},
    )
    sess.commit()

    response = client.delete(f"/g/supplier_contracts/{contract.id}/edit")
    assert response.headers["HX-Redirect"].endswith("/g/supplier_contracts")


def test_supplies(client, sess):
    response = client.get("/g/supplies")

    match(response, 200)


def test_supply_get(client, sess):
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    g_contract = GContract.insert_supplier(
        sess, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    g_supply = site.insert_g_supply(
        sess,
        "7y94u5",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    sess.commit()

    response = client.get(f"/g/supplies/{g_supply.id}")

    match(response, 200)


def test_supply_get_bill_after_end(client, sess):
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    g_contract = GContract.insert_supplier(
        sess, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    g_supply = site.insert_g_supply(
        sess,
        "7y94u5",
        "main",
        g_exit_zone,
        to_utc(ct_datetime(2018, 1, 1)),
        to_utc(ct_datetime(2018, 1, 10)),
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )
    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    insert_bill_types(sess)

    bill_type_n = BillType.get_by_code(sess, "N")

    g_batch.insert_g_bill(
        sess,
        g_supply,
        bill_type_n,
        "55h883",
        "dhgh883",
        utc_datetime(2019, 4, 3),
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31, 23, 30),
        Decimal("45"),
        Decimal("12.40"),
        Decimal("1.20"),
        Decimal("14.52"),
        "",
        {},
    )

    sess.commit()

    response = client.get(f"/g/supplies/{g_supply.id}")
    patterns = [r'<td rowspan="1">\s*' r'<a href="/g/bills/1">view</a>\s*' r"</td>"]

    match(response, 200, *patterns)


def test_supply_note_add_get(client, sess):
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")

    g_ldz = g_dn.insert_g_ldz(sess, "EA")

    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")

    insert_g_units(sess)

    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    g_contract = GContract.insert_supplier(
        sess, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    g_supply = site.insert_g_supply(
        sess,
        "7y94u5",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    sess.commit()

    response = client.get(f"/g/supplies/{g_supply.id}/notes/add")

    match(response, 200)


def test_supply_notes_get(client, sess):
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")

    g_ldz = g_dn.insert_g_ldz(sess, "EA")

    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")

    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    g_contract = GContract.insert_supplier(
        sess, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    g_supply = site.insert_g_supply(
        sess,
        "7y94u5",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )
    sess.commit()

    response = client.get(f"/g/supplies/{g_supply.id}/notes")

    match(response, 200)


def test_supply_edit_post(client, sess):
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    g_contract = GContract.insert_supplier(
        sess, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    g_supply = site.insert_g_supply(
        sess,
        "7y94u5",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    sess.commit()

    data = {
        "insert_g_era": "Insert",
        "start_year": "2022",
        "start_month": "01",
        "start_day": "01",
        "start_hour": "00",
        "start_minute": "00",
    }

    response = client.post(f"/g/supplies/{g_supply.id}/edit", data=data)
    assert response.headers["Location"] == f"/g/supplies/{g_supply.id}"

    match(response, 303)


def test_read_edit_post_delete(sess, client):
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")

    g_ldz = g_dn.insert_g_ldz(sess, "EA")

    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")

    insert_g_units(sess)

    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    insert_g_reading_frequencies(sess)

    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    g_supply = site.insert_g_supply(
        sess,
        "7y94u5",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    insert_bill_types(sess)

    bill_type_n = BillType.get_by_code(sess, "N")

    g_bill = g_batch.insert_g_bill(
        sess,
        g_supply,
        bill_type_n,
        "55h883",
        "dhgh883",
        utc_datetime(2019, 4, 3),
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31, 23, 30),
        Decimal("45"),
        Decimal("12.40"),
        Decimal("1.20"),
        Decimal("14.52"),
        "",
        {},
    )

    insert_g_read_types(sess)

    g_read_type_A = GReadType.get_by_code(sess, "A")

    g_read = g_bill.insert_g_read(
        sess,
        "ghu5438gt",
        g_unit_M3,
        1,
        37,
        Decimal(800),
        utc_datetime(2020, 1, 1),
        g_read_type_A,
        Decimal(900),
        utc_datetime(2020, 1, 31),
        g_read_type_A,
    )

    sess.commit()

    data = {
        "delete": "Delete",
    }

    response = client.post(f"/g/reads/{g_read.id}/edit", data=data)

    match(response, 303, f"/g/bills/{g_bill.id}")


def test_supply_edit_get(client, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    g_contract = GContract.insert_supplier(sess, "Fusion 2020", "", {}, vf, None, {})

    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    g_supply = site.insert_g_supply(
        sess,
        "7y94u5",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    sess.commit()

    response = client.get(f"/g/supplies/{g_supply.id}/edit")
    match(response, 200, r'<option value="1" selected>EA1</option>')


def test_supplier_rate_script_get(sess, client):
    g_contract = GContract.insert(
        sess,
        False,
        "Fusion 2020",
        "",
        {},
        utc_datetime(2019, 1, 1),
        utc_datetime(2019, 2, 28, 23, 30),
        {},
    )

    g_contract.insert_g_rate_script(sess, utc_datetime(2019, 2, 1), {})
    g_rate_script = g_contract.insert_g_rate_script(sess, utc_datetime(2019, 2, 2), {})

    sess.commit()

    response = client.get(f"/g/supplier_rate_scripts/{g_rate_script.id}")

    match(response, 200, "Previous Rate Script")


def test_supplier_rate_script_edit_post_delete(sess, client):
    g_contract = GContract.insert(
        sess,
        False,
        "Fusion 2020",
        "",
        {},
        utc_datetime(2019, 1, 1),
        utc_datetime(2019, 2, 28, 23, 30),
        {},
    )

    g_rate_script = g_contract.insert_g_rate_script(sess, utc_datetime(2019, 2, 1), {})

    sess.commit()

    data = {
        "delete": "Delete",
    }

    response = client.post(
        f"/g/supplier_rate_scripts/{g_rate_script.id}/edit", data=data
    )

    match(response, 303, f"/g/supplier_contracts/{g_contract.id}")


def test_read_add_get(sess, client):
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")

    g_ldz = g_dn.insert_g_ldz(sess, "EA")

    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")

    insert_g_units(sess)

    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    insert_g_reading_frequencies(sess)

    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    g_supply = site.insert_g_supply(
        sess,
        "7y94u5",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    insert_bill_types(sess)

    bill_type_n = BillType.get_by_code(sess, "N")

    g_bill = g_batch.insert_g_bill(
        sess,
        g_supply,
        bill_type_n,
        "55h883",
        "dhgh883",
        utc_datetime(2019, 4, 3),
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31, 23, 30),
        Decimal("45"),
        Decimal("12.40"),
        Decimal("1.20"),
        Decimal("14.52"),
        "",
        {},
    )

    sess.commit()

    response = client.get(f"/g/bills/{g_bill.id}/edit")

    match(response, 200)


def test_read_add_post(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    g_contract = GContract.insert(sess, False, "Fusion 2020", "", {}, vf, None, {})

    g_supply = site.insert_g_supply(
        sess,
        "7y94u5",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    insert_bill_types(sess)

    bill_type_n = BillType.get_by_code(sess, "N")

    g_bill = g_batch.insert_g_bill(
        sess,
        g_supply,
        bill_type_n,
        "55h883",
        "dhgh883",
        utc_datetime(2019, 4, 3),
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31, 23, 30),
        Decimal("45"),
        Decimal("12.40"),
        Decimal("1.20"),
        Decimal("14.52"),
        "",
        {},
    )
    insert_g_read_types(sess)
    g_read_type_A = GReadType.get_by_code(sess, "A")

    sess.commit()

    data = {
        "msn": "fjshkk",
        "g_unit_id": g_unit_M3.id,
        "correction_factor": 1,
        "calorific_value": 1,
        "prev_date_year": 2020,
        "prev_date_month": 1,
        "prev_date_day": 4,
        "prev_date_hour": 0,
        "prev_date_minute": 0,
        "prev_value": 20,
        "prev_type_id": g_read_type_A.id,
        "pres_date_year": 2020,
        "pres_date_month": 1,
        "pres_date_day": 9,
        "pres_date_hour": 0,
        "pres_date_minute": 0,
        "pres_value": 25,
        "pres_type_id": g_read_type_A.id,
    }

    response = client.post(f"/g/bills/{g_bill.id}/add_read", data=data)

    match(response, 303)


def test_era_edit_get(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    GContract.insert(sess, True, "Unidentified gas", "", {}, vf, None, {})
    g_contract = GContract.insert(sess, False, "Fusion 2020", "", {}, vf, None, {})

    g_supply = site.insert_g_supply(
        sess,
        "7y94u5",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    g_era = g_supply.g_eras[0]

    sess.commit()

    response = client.get(f"/g/eras/{g_era.id}/edit")

    match(
        response,
        200,
        r'<select name="g_contract_id">\s*'
        r'<option value="2" selected>Fusion 2020</option>\s*'
        r"</select>",
    )


def test_era_post(sess, client):
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")

    g_ldz = g_dn.insert_g_ldz(sess, "EA")

    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")

    insert_g_units(sess)

    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    insert_g_reading_frequencies(sess)

    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    g_supply = site.insert_g_supply(
        sess,
        "7y94u5",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    g_era = g_supply.g_eras[0]

    sess.commit()

    data = {
        "start_year": "2018",
        "start_month": "01",
        "start_day": "01",
        "start_hour": "0",
        "start_minute": "0",
        "msn": "9874h6l",
        "correction_factor": "1",
        "g_contract_id": g_contract.id,
        "account": "acc 8",
        "g_unit_id": g_unit_M3.id,
        "g_reading_frequency_id": g_reading_frequency_M.id,
        "aq": 1,
        "soq": 1,
    }

    response = client.post(f"/g/eras/{g_era.id}/edit", data=data)

    match(response, 303, r"/g/supplies/1")


def test_era_post_delete(sess, client):
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")

    g_ldz = g_dn.insert_g_ldz(sess, "EA")

    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")

    insert_g_units(sess)

    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    insert_g_reading_frequencies(sess)

    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )

    g_supply = site.insert_g_supply(
        sess,
        "7y94u5",
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    g_era = g_supply.insert_g_era_at(sess, utc_datetime(2018, 3, 1))

    sess.commit()

    data = {
        "delete": "Delete",
    }

    response = client.post(f"/g/eras/{g_era.id}/edit", data=data)

    match(response, 303, r"/g/supplies/1")
