from flask import g
from flask_restx import Api, Resource, fields, inputs, reqparse

from sqlalchemy import null, or_, select

import chellow.reports.report_247
from chellow.models import (
    Channel,
    Era,
    HhDatum,
    ReportRun,
    ReportRunRow,
    Site,
    Source,
    Supply,
)
from chellow.utils import to_utc

api = Api(
    version="1.0",
    title="Chellow API",
    description="Access Chellow data",
    endpoint="/api/v1",
    doc="/api/v1",
)

ns = api.namespace("v1", path="/api/v1/")

generator_type_model = ns.model(
    "GeneratorType",
    {
        "id": fields.Integer(example="884"),
        "code": fields.String(example="gen"),
        "description": fields.String(example=""),
    },
)

gsp_group_model = ns.model(
    "GspGroup",
    {
        "id": fields.Integer(example="884"),
        "code": fields.String(example="gen"),
        "name": fields.String(example=""),
    },
)

dno_group_model = ns.model(
    "Dno",
    {
        "id": fields.Integer(example="884"),
        "dno_code": fields.String(example="22"),
    },
)

sites__model = ns.model(
    "Site",
    {
        "id": fields.Integer(example="884"),
        "code": fields.String(example="GGJ23"),
        "name": fields.String(example="Trowbridge Waterworks"),
    },
)

site__era__model = ns.model(
    "Era",
    {
        "id": fields.Integer(example="81"),
        "supply_id": fields.Integer(example="988"),
        "start_date": fields.DateTime(example="2019-05-18T15:17:00+00:00"),
        "finish_date": fields.DateTime(example="2019-06-10T11:17:00+00:00"),
        "imp_mpan_core": fields.String,
        "exp_mpan_core": fields.String,
    },
)

site__site_era__model = ns.model(
    "SiteEra",
    {
        "id": fields.Integer(example="74"),
        "era": fields.Nested(site__era__model),
        "is_physical": fields.Boolean(example="true"),
    },
)

site__model = ns.model(
    "Site",
    {
        "id": fields.Integer(example="884"),
        "code": fields.String(example="GGJ23"),
        "name": fields.String(example="Trowbridge Waterworks"),
        "site_eras": fields.List(fields.Nested(site__site_era__model)),
    },
)

source_model = ns.model(
    "Source",
    {
        "id": fields.Integer(example="884"),
        "code": fields.String(example="GGJ23"),
        "name": fields.String(example="Trowbridge Waterworks"),
    },
)
hh_data_model = ns.model(
    "HhData",
    {
        "from": fields.Integer,
        "to": fields.String,
        "name": fields.String,
    },
)

eras__site__model = ns.model(
    "Site",
    {
        "id": fields.Integer(example="884"),
        "code": fields.String(example="GGJ23"),
        "name": fields.String(example="Trowbridge Waterworks"),
    },
)

eras__site_eras__model = ns.model(
    "SiteEra",
    {
        "id": fields.Integer(example="74"),
        "site": fields.Nested(eras__site__model),
        "is_physical": fields.Boolean(example="true"),
    },
)

eras__mop_contract__model = ns.model(
    "MOP Contract",
    {
        "id": fields.Integer(example="821"),
        "name": fields.String(example="Marmaduke's Metering"),
    },
)

eras__dc_contract__model = ns.model(
    "DC Contract",
    {
        "id": fields.Integer(example="821"),
        "name": fields.String(example="Daisy's Data Collection"),
    },
)

pc__model = ns.model(
    "Profile Class",
    {
        "id": fields.Integer(example="8"),
        "code": fields.String(example="00"),
        "description": fields.String(example="Half-hourly"),
    },
)

era__participant__model = ns.model(
    "Participant",
    {
        "id": fields.Integer(example="91"),
        "code": fields.String(example="CUST"),
        "name": fields.String(example="Ingram Enterprises"),
    },
)

era__dno__model = ns.model(
    "DNO",
    {
        "id": fields.Integer(example="8"),
        "dno_code": fields.String(example="33"),
    },
)


era__mtc__model = ns.model(
    "Meter Timeswitch Class",
    {
        "id": fields.Integer(example="89"),
        "code": fields.String(example="800"),
        "description": fields.String(example="Unmetered"),
    },
)

cop__model = ns.model(
    "Code Of Practice",
    {
        "id": fields.Integer(example="89"),
        "code": fields.String(example="6c"),
        "description": fields.String(example="NHH"),
    },
)

eras__model = ns.model(
    "Eras",
    {
        "id": fields.Integer(example="712"),
        "supply_id": fields.Integer(example="349"),
        "site_eras": fields.List(fields.Nested(eras__site_eras__model)),
        "start_date": fields.DateTime(example="2019-05-18T15:17:00+00:00"),
        "finish_date": fields.DateTime(example="2019-06-10T11:17:00+00:00"),
    },
)


era__clock_interval__model = ns.model(
    "Clock Interval",
    {
        "id": fields.Integer(example="920"),
        "day_of_week": fields.Integer(example="2"),
        "start_month": fields.Integer(example="10"),
        "start_day": fields.Integer(example="23"),
        "start_hour": fields.Integer(example="23"),
        "start_minute": fields.Integer(example="30"),
        "end_month": fields.Integer(example="12"),
        "end_day": fields.Integer(example="13"),
        "end_hour": fields.Integer(example="6"),
        "end_minute": fields.Integer(example="0"),
    },
)

era__tpr__model = ns.model(
    "Tariff Pattern Regime",
    {
        "id": fields.Integer(example="71"),
        "code": fields.String(example="00001"),
        "is_teleswitch": fields.Boolean(example="false"),
        "is_gmt": fields.Boolean(example="true"),
        "clock_intervals": fields.List(fields.Nested(era__clock_interval__model)),
    },
)


measurement_requirement__model = ns.model(
    "Measurement Requirement",
    {
        "id": fields.Integer(example="72"),
        "tpr": fields.Nested(era__tpr__model),
    },
)

ssc__model = ns.model(
    "Standard Settlement Configuration",
    {
        "id": fields.Integer(example="11"),
        "code": fields.String(example="0363"),
        "description": fields.String(example="Unrestricted"),
        "is_import": fields.Boolean(example="true"),
        "valid_from": fields.DateTime(example="2019-05-18T15:17:00+00:00"),
        "valid_to": fields.DateTime(example="2019-05-18T15:17:00+00:00"),
        "measurement_requirements": fields.List(
            fields.Nested(measurement_requirement__model)
        ),
    },
)

energisation_status__model = ns.model(
    "Energisation Status",
    {
        "id": fields.Integer(example="25"),
        "code": fields.String(example="E"),
        "description": fields.String(example="Energised"),
    },
)

era__llfc__model = ns.model(
    "Line Loss Factor Class",
    {
        "id": fields.Integer(example="54"),
        "code": fields.String(example="010"),
        "description": fields.String(example="HV Sub"),
    },
)

era__supplier_contract__model = ns.model(
    "Supplier Contract",
    {
        "id": fields.Integer(example="871"),
        "name": fields.String(example="High Charges"),
    },
)


era__mop_contract__model = ns.model(
    "MOP Contract",
    {
        "id": fields.Integer(example="821"),
        "name": fields.String(example="Marmaduke's Metering"),
    },
)

hh_datum_model = ns.model(
    "HH Datum",
    {
        "id": fields.Integer(example="871"),
        "start_date": fields.DateTime(example="2019-05-18T15:17:00+00:00"),
        "value": fields.String(example="0.01"),
        "last_modified": fields.DateTime(example="2019-05-18T15:00:00+00:00"),
    },
)


def hh_datum_to_j(hh_datum):
    return {
        "id": hh_datum.id,
        "start_date": hh_datum.start_date,
        "value": hh_datum.value,
        "last_modified": hh_datum.last_modified,
    }


channel_model = ns.model(
    "Channel",
    {
        "id": fields.Integer(example="871"),
        "imp_related": fields.Boolean(example="true"),
        "channel_type": fields.String(example="ACTIVE"),
        "hh_data": fields.List(fields.Nested(hh_datum_model)),
    },
)


def channel_to_j(channel):
    return {
        "id": channel.id,
        "era_id": channel.era_id,
        "imp_related": channel.imp_related,
        "channel_type": channel.channel_type,
    }


era__model = ns.model(
    "Era",
    {
        "id": fields.Integer(example="712"),
        "supply_id": fields.Integer(example="349"),
        "site_eras": fields.List(fields.Nested(eras__site_eras__model)),
        "start_date": fields.DateTime(example="2019-05-18T15:17:00+00:00"),
        "finish_date": fields.DateTime(example="2019-06-10T11:17:00+00:00"),
        "mop_contract": fields.Nested(era__mop_contract__model),
        "mop_account": fields.String(example="xc771"),
        "dc_contract": fields.Nested(eras__dc_contract__model),
        "dc_account": fields.String(example="703n"),
        "msn": fields.String(example="mn88hg2"),
        "pc": fields.Nested(pc__model),
        "mtc": fields.Nested(era__mtc__model),
        "cop": fields.Nested(cop__model),
        "ssc": fields.Nested(ssc__model),
        "energisation_status": fields.Nested(energisation_status__model),
        "properties": fields.String,
        "imp_mpan_core": fields.String(example="22 5478 7392 943"),
        "imp_llfc": fields.Nested(era__llfc__model),
        "imp_supplier_contract": fields.Nested(era__supplier_contract__model),
        "imp_supplier_account": fields.String(example="x66g"),
        "imp_sc": fields.Integer(example="700"),
        "exp_mpan_core": fields.String(example="22 8672 2951 081"),
        "exp_llfc": fields.Nested(era__llfc__model),
        "exp_supplier_contract": fields.Nested(era__supplier_contract__model),
        "exp_supplier_account": fields.String(example="h8892"),
        "exp_sc": fields.Integer(example="900"),
        "channels": fields.List(fields.Nested(channel_model)),
    },
)


channel_model = ns.model(
    "Channel",
    {
        "id": fields.Integer(example="871"),
        "imp_related": fields.Boolean(example="true"),
        "channel_type": fields.String(example="ACTIVE"),
        "hh_data": fields.List(fields.Nested(hh_datum_model)),
    },
)


def report_run_row_to_j(report_run_row):
    return {
        "id": report_run_row.id,
        "report_run_id": report_run_row.report_run_id,
        "tab": report_run_row.tab,
        "data": report_run_row.data,
    }


report_run_row_model = ns.model(
    "ReportRunRow",
    {
        "id": fields.Integer(example="712"),
        "report_run_id": fields.Integer(example="782"),
        "tab": fields.String(example="sites"),
        "data": fields.Raw(),
    },
)


def report_run_to_j(report_run):
    return {
        "id": report_run.id,
        "date_created": report_run.date_created,
        "creator": report_run.creator,
        "name": report_run.name,
        "title": report_run.title,
        "state": report_run.state,
        "data": report_run.data,
    }


report_run_model = ns.model(
    "ReportRun",
    {
        "id": fields.Integer(example="712"),
        "date_created": fields.DateTime(example="2019-05-18T15:17:00+00:00"),
        "creator": fields.String(example="H. G. Wells"),
        "name": fields.String(example="bill_check"),
        "title": fields.String(example="batch_55-00"),
        "state": fields.Raw(),
        "data": fields.Raw(),
        "rows": fields.List(fields.Nested(report_run_row_model)),
    },
)


@ns.route("/sites")
class SitesResource(Resource):
    @api.marshal_list_with(sites__model)
    def get(self):
        return g.sess.query(Site).order_by(Site.code).all()


@ns.route("/sites/<int:site_id>")
@ns.param("site_id", "The site identifier")
class SiteResource(Resource):
    @api.marshal_with(site__model)
    def get(self, site_id):
        return Site.get_by_id(g.sess, site_id)


@ns.route("/eras/<int:era_id>")
class EraResource(Resource):
    @api.marshal_with(era__model)
    def get(self, era_id):
        return Era.get_by_id(g.sess, era_id)


channel_get_parser = reqparse.RequestParser()
channel_get_parser.add_argument(
    "from",
    type=inputs.datetime_from_iso8601,
    help="Beginning of date range for half-hourly data.",
)
channel_get_parser.add_argument(
    "to",
    type=inputs.datetime_from_iso8601,
    help="End of date range for half-hourly data.",
)


channel_parser = ns.parser()
channel_parser.add_argument(
    "start_date",
    type=inputs.datetime_from_iso8601,
    required=True,
    help="Start of HH data",
    default="2025-12-01T00:00Z",
)
channel_parser.add_argument(
    "finish_date",
    type=inputs.datetime_from_iso8601,
    required=True,
    help="Finish of HH data",
    default="2025-12-31T23:30Z",
)


@ns.route("/channel/<int:channel_id>")
class ChannelResource(Resource):
    @api.marshal_with(channel_model)
    @ns.expect(channel_parser)
    def get(self, channel_id):
        args = channel_parser.parse_args()
        start_date = to_utc(args["start_date"])
        finish_date = to_utc(args["finish_date"])
        channel = Channel.get_by_id(g.sess, channel_id)
        channel_j = channel_to_j(channel)
        hh_data_j = []
        for hh_datum in g.sess.scalars(
            select(HhDatum).where(
                HhDatum.channel == channel,
                HhDatum.start_date >= start_date,
                HhDatum.start_date <= finish_date,
            )
        ):
            hh_data_j.append(hh_datum_to_j(hh_datum))
        channel_j["hh_data"] = hh_data_j
        return channel_j


supply_model = ns.model(
    "Supply",
    {
        "id": fields.Integer(example="712"),
        "name": fields.String(example="hgeoiu"),
        "source": fields.Nested(source_model),
        "generator_type": fields.Nested(generator_type_model, required=False),
        "gsp_group": fields.Nested(gsp_group_model),
        "dno": fields.Nested(dno_group_model),
        "eras": fields.List(fields.Nested(era__model)),
    },
)

supplies_parser = ns.parser()
supplies_parser.add_argument(
    "start_date",
    type=inputs.datetime_from_iso8601,
    required=True,
    help="Start of eras, channels and HH data",
    default="2025-12-01T00:00Z",
)
supplies_parser.add_argument(
    "finish_date",
    type=inputs.datetime_from_iso8601,
    required=True,
    help="Finish of eras, channales and HH data",
    default="2025-12-31T23:30Z",
)
supplies_parser.add_argument("source_code", type=str, default="gen")


@ns.route("/supplies")
class SuppliesResource(Resource):
    @api.marshal_list_with(supply_model)
    @ns.expect(supplies_parser)
    def get(self):
        args = supplies_parser.parse_args()
        start_date = to_utc(args["start_date"])
        finish_date = to_utc(args["finish_date"])

        supplies_j = []
        supplies_q = (
            select(Supply)
            .join(Era)
            .where(
                Era.start_date <= finish_date,
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
            )
            .distinct()
        )
        if "source_code" in args:
            supplies_q = supplies_q.join(Source).where(
                Source.code == args["source_code"]
            )
        for supply in g.sess.scalars(supplies_q):
            eras_j = []
            supply_j = {
                "id": supply.id,
                "name": supply.name,
                "source": supply.source,
                "generator_type": supply.generator_type,
                "gsp_group": supply.gsp_group,
                "dno": supply.dno,
                "eras": eras_j,
            }
            supplies_j.append(supply_j)
            for era in g.sess.scalars(
                select(Era)
                .where(
                    Era.supply == supply,
                    Era.start_date <= finish_date,
                    or_(Era.finish_date == null(), Era.finish_date >= start_date),
                )
                .order_by(Era.start_date)
            ):
                channels_j = []
                era_j = {
                    "id": era.id,
                    "site_eras": era.site_eras,
                    "start_date": era.start_date,
                    "finish_date": era.finish_date,
                    "mop_contract": era.mop_contract,
                    "dc_contract": era.dc_contract,
                    "msn": era.msn,
                    "pc": era.pc,
                    "mtc_participant": era.mtc_participant,
                    "cop": era.cop,
                    "ssc": era.ssc,
                    "energisation_status": era.energisation_status,
                    "imp_mpan_core": era.imp_mpan_core,
                    "imp_llfc": era.imp_llfc,
                    "imp_supplier_contract": era.imp_supplier_contract,
                    "imp_supplier_account": era.imp_supplier_account,
                    "imp_sc": era.imp_sc,
                    "exp_mpan_core": era.exp_mpan_core,
                    "exp_llfc": era.exp_llfc,
                    "exp_supplier_contract": era.exp_supplier_contract,
                    "exp_supplier_account": era.exp_supplier_account,
                    "exp_sc": era.exp_sc,
                    "channels": channels_j,
                }
                eras_j.append(era_j)
                for channel in era.channels:

                    channel_j = {
                        "id": channel.id,
                        "era_id": channel.era_id,
                        "imp_related": channel.imp_related,
                        "channel_type": channel.channel_type,
                    }
                    channels_j.append(channel_j)
        return supplies_j


supply_parser = ns.parser()
supply_parser.add_argument(
    "start_date",
    type=inputs.datetime_from_iso8601,
    required=True,
    help="Start of HH data",
    default="2025-12-01T00:00Z",
)
supply_parser.add_argument(
    "finish_date",
    type=inputs.datetime_from_iso8601,
    required=True,
    help="Finish of HH data",
    default="2025-12-31T23:30Z",
)


@ns.route("/supplies/<int:supply_id>")
class SupplyResource(Resource):
    @api.marshal_with(supply_model)
    @ns.expect(supply_parser)
    def get(self, supply_id):
        args = supply_parser.parse_args()
        start_date = to_utc(args["start_date"])
        finish_date = to_utc(args["finish_date"])

        supply = Supply.get_by_id(g.sess, supply_id)
        eras_j = []
        supply_j = {
            "id": supply.id,
            "name": supply.name,
            "source": supply.source,
            "generator_type": supply.generator_type,
            "gsp_group": supply.gsp_group,
            "dno": supply.dno,
            "eras": eras_j,
        }
        for era in g.sess.scalars(
            select(Era)
            .where(
                Era.supply == supply,
                Era.start_date <= finish_date,
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
            )
            .order_by(Era.start_date)
        ):
            channels_j = []
            era_j = {
                "id": era.id,
                "site_eras": era.site_eras,
                "start_date": era.start_date,
                "finish_date": era.finish_date,
                "mop_contract": era.mop_contract,
                "dc_contract": era.dc_contract,
                "msn": era.msn,
                "pc": era.pc,
                "mtc_participant": era.mtc_participant,
                "cop": era.cop,
                "ssc": era.ssc,
                "energisation_status": era.energisation_status,
                "imp_mpan_core": era.imp_mpan_core,
                "imp_llfc": era.imp_llfc,
                "imp_supplier_contract": era.imp_supplier_contract,
                "imp_supplier_account": era.imp_supplier_account,
                "imp_sc": era.imp_sc,
                "exp_mpan_core": era.exp_mpan_core,
                "exp_llfc": era.exp_llfc,
                "exp_supplier_contract": era.exp_supplier_contract,
                "exp_supplier_account": era.exp_supplier_account,
                "exp_sc": era.exp_sc,
                "channels": channels_j,
            }
            eras_j.append(era_j)
            for channel in era.channels:

                channel_j = {
                    "id": channel.id,
                    "era_id": channel.era_id,
                    "imp_related": channel.imp_related,
                    "channel_type": channel.channel_type,
                }
                hh_data_j = []
                for hh_datum in g.sess.scalars(
                    select(HhDatum)
                    .where(
                        HhDatum.channel == channel,
                        HhDatum.start_date >= start_date,
                        HhDatum.start_date <= finish_date,
                    )
                    .order_by(HhDatum.start_date)
                ):
                    hh_datum_j = {
                        "id": hh_datum.id,
                        "start_date": hh_datum.start_date,
                        "value": hh_datum.value,
                        "last_modified": hh_datum.last_modified,
                    }
                    hh_data_j.append(hh_datum_j)
                channel_j["hh_data"] = hh_data_j

                channels_j.append(channel_j)
        return supply_j


@ns.route("/eras")
class ErasResource(Resource):
    @api.marshal_list_with(eras__model)
    def get(self):
        return (
            g.sess.query(Era).filter(Era.finish_date == null()).order_by(Era.id).all()
        )


report_model = ns.model(
    "Report",
    {
        "report_run_id": fields.Integer(example="712"),
    },
)

report_monthly_duration_parser = ns.parser()
report_monthly_duration_parser.add_argument(
    "finish_year",
    type=int,
    help="Finish year of period",
    default="2025",
)
report_monthly_duration_parser.add_argument(
    "finish_month",
    type=int,
    help="Finish month of period",
    default="12",
)
report_monthly_duration_parser.add_argument(
    "months",
    type=int,
    help="Duration of period",
    default="1",
)


@ns.route("/reports/monthly_duration")
class ReportMonthlyDurationResource(Resource):
    @api.marshal_with(report_model)
    @ns.expect(report_monthly_duration_parser)
    def get(self):
        args = report_monthly_duration_parser.parse_args()
        return chellow.reports.report_247.do_get_j(args)


report_runs_parser = ns.parser()


@ns.route("/report_runs")
class ReportRunsResource(Resource):
    @api.marshal_list_with(report_run_model)
    @ns.expect(report_runs_parser)
    def get(self):
        report_runs_parser.parse_args()

        report_runs_j = []
        for report_run in g.sess.scalars(select(ReportRun)):
            report_runs_j.append(report_run_to_j(report_run))
        return report_runs_j


report_run_parser = ns.parser()
report_run_parser.add_argument(
    "include_rows",
    type=inputs.boolean,
    help="Show report rows in the response",
    default="false",
)


@ns.route("/report_runs/<int:report_run_id>")
class ReportRunResource(Resource):
    @api.marshal_list_with(report_run_model)
    @ns.expect(report_run_parser)
    def get(self, report_run_id):
        report_run_parser.parse_args()
        report_run_j = report_run_to_j(ReportRun.get_by_id(g.sess, report_run_id))
        rows = []
        for row in g.sess.scalars(
            select(ReportRunRow).where(ReportRunRow.report_run_id == report_run_id)
        ):
            rows.append(report_run_row_to_j(row))
        report_run_j["rows"] = rows
        return report_run_j
