from flask import g

from flask_restx import Api, Resource, fields, inputs, reqparse

from sqlalchemy import null, select

from chellow.models import Channel, Era, HhDatum, Site


api = Api(
    version="1.0",
    title="Chellow API",
    description="Access Chellow data",
    endpoint="/api/v1",
    doc="/api/v1",
)

ns = api.namespace("v1", path="/api/v1/")

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


era__channel__model = ns.model(
    "Channel",
    {
        "id": fields.Integer(example="871"),
        "imp_related": fields.Boolean(example="true"),
        "channel_type": fields.String(example="ACTIVE"),
    },
)


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
        "channels": fields.List(fields.Nested(era__channel__model)),
    },
)


channel__hh_datum__model = ns.model(
    "HH Datum",
    {
        "id": fields.Integer(example="871"),
        "channel_type": fields.String(example="ACTIVE"),
        "start_date": fields.DateTime(example="2019-05-18T15:17:00+00:00"),
        "value": fields.String(example="0.01"),
        "last_modified_date": fields.DateTime(example="2019-05-18T15:17:00+00:00"),
    },
)


channel__model = ns.model(
    "Channel",
    {
        "id": fields.Integer(example="871"),
        "imp_related": fields.Boolean(example="true"),
        "channel_type": fields.String(example="ACTIVE"),
        "hh_data": fields.List(fields.Nested(channel__hh_datum__model)),
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


@ns.route("/channel/<int:channel_id>")
@ns.param("from", "YYYY-mm-dd HH:MM")
@ns.param("to", "YYYY-mm-dd HH:MM")
class ChannelResource(Resource):
    @api.marshal_with(channel__model)
    def get(self, channel_id):
        args = channel_get_parser.parse_args()
        channel = Channel.get_by_id(g.sess, channel_id)
        channel_j = {
            "id": channel.id,
            "era_id": channel.era_id,
            "imp_related": channel.imp_related,
            "channel_type": channel.channel_type,
        }
        channel_j["hh_data"] = g.sess.execute(
            select(HhDatum).where(
                HhDatum.channel == channel,
                HhDatum.start_date >= args["from"],
                HhDatum.start_date <= args["to"],
            )
        ).all()
        return channel_j


@ns.route("/eras")
class ErasResource(Resource):
    @api.marshal_list_with(eras__model)
    def get(self):
        return (
            g.sess.query(Era).filter(Era.finish_date == null()).order_by(Era.id).all()
        )
