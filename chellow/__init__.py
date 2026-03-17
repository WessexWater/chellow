import os
from datetime import datetime as Datetime
from importlib.metadata import version
from pathlib import Path

from flask import Flask, g, make_response, render_template, request

from markdown_it import MarkdownIt

from markupsafe import Markup

from sqlalchemy import select

from werkzeug.exceptions import BadRequest, NotFound

from zish import ZishException, dumps

import chellow.api
import chellow.bank_holidays
import chellow.dloads
import chellow.e.bmarketidx
import chellow.e.elexon
import chellow.e.hh_importer
import chellow.e.isd
import chellow.e.neso
import chellow.e.rcrc
import chellow.e.system_price
import chellow.e.views
import chellow.fake_batch_updater
import chellow.gas.cv
import chellow.gas.views
import chellow.rrun
import chellow.testing
from chellow.auth import set_user_func
from chellow.models import (
    Contract,
    Session,
    User,
    db_upgrade,
    start_sqlalchemy,
)
from chellow.utils import HH, ct_datetime, date_format, to_ct, utc_datetime_now


def get_importer_modules():
    return (
        chellow.e.isd,
        chellow.e.elexon,
        chellow.e.lccc,
        chellow.testing,
        chellow.bank_holidays,
        chellow.gas.cv,
        chellow.e.bmarketidx,
        chellow.e.neso,
        chellow.rate_server,
        chellow.rrun,
        chellow.fake_batch_updater,
    )


def create_app(testing=False, instance_path=None):
    app = Flask("chellow", instance_relative_config=True, instance_path=instance_path)
    app.config["RESTX_VALIDATE"] = True
    app.wsgi_app = set_user_func(app.wsgi_app)
    app.secret_key = os.urandom(24)
    start_sqlalchemy()

    app.register_blueprint(chellow.views.home)
    app.register_blueprint(chellow.e.views.e)
    app.register_blueprint(chellow.gas.views.gas)

    api = chellow.api.api
    api.init_app(app, endpoint="/api/v1")

    if not testing:
        db_upgrade(app.root_path)
        chellow.e.hh_importer.startup()

        with Session() as sess:
            configuration = sess.execute(
                select(Contract).where(Contract.name == "configuration")
            ).scalar_one()
            props = configuration.make_properties()
            api_props = props.get("api", {})
            api.description = api_props.get("description", "Access Chellow data")

    chellow.dloads.startup(Path(app.instance_path), run_deleter=(not testing))

    for module in get_importer_modules():
        if not testing:
            module.startup()

    @app.before_request
    def before_request():
        g.sess = Session()

        msg = " ".join(
            "-" if v is None else v
            for v in (
                request.remote_addr,
                str(request.user_agent),
                request.remote_user,
                f"[{Datetime.now().strftime('%d/%b/%Y:%H:%M:%S')}]",
                f'"{request.method} {request.path} '
                f'{request.environ.get("SERVER_PROTOCOL")}"',
                None,
                None,
            )
        )
        print(msg)

    @app.before_request
    def get_user(*args, **kwargs):
        g.user = None
        username = request.environ.get("REMOTE_USER")
        if username is None:
            username = "viewer"
        user = g.sess.scalars(
            select(User).where(User.username == username)
        ).one_or_none()
        if user is None:
            user = g.sess.scalars(
                select(User).where(User.username == "viewer")
            ).one_or_none()
            if user is None:
                raise BadRequest("The default user 'viewer' is not set up in Chellow.")
        g.user = user
        config_contract = Contract.get_non_core_by_name(g.sess, "configuration")
        try:
            g.config = config_contract.make_properties()
        except ZishException:
            g.config = {}

    @app.before_request
    def check_permissions(*args, **kwargs):
        method = request.method

        role_code = g.user.user_role.code
        path = request.path

        if (
            role_code == "viewer"
            and (
                method in ("GET", "HEAD")
                or path
                in (
                    "/reports/59",
                    "/reports/169",
                    "/reports/183",
                    "/reports/187",
                    "/reports/247",
                    "/reports/111",
                    "/reports/149",
                )
                or path.startswith("/api/")
            )
            and path not in ("/system",)
        ):
            return
        elif role_code == "editor":
            return
        elif role_code == "party-viewer":
            if method in ("GET", "HEAD"):
                party = g.user.party
                market_role_code = party.market_role.code
                if market_role_code in ("C", "D"):
                    dc_contract_id = request.args["dc_contract_id"]
                    dc_contract = Contract.get_dc_by_id(g.sess, dc_contract_id)
                    if dc_contract.party == party and request.full_path.startswith(
                        "/channel_snags?"
                    ):
                        return
                elif market_role_code == "X":
                    if path.startswith(f"/e/supplier_contracts/{party.id}"):
                        return

        return make_response(render_template("403.html", properties=g.config), 403)

    @app.context_processor
    def chellow_context_processor():

        global_alerts = []
        for task in chellow.e.hh_importer.tasks.values():
            if task.is_error:
                try:
                    contract = Contract.get_by_id(g.sess, task.contract_id)
                    global_alerts.append(
                        f"There's a problem with the <a "
                        f"href='/e/dc_contracts/{contract.id}/auto_importer'>"
                        f"automatic HH data importer for contract '{contract.name}'"
                        f"</a>.",
                    )
                except NotFound:
                    pass

        for mod in get_importer_modules():
            importer = mod.get_importer()
            if importer is not None and importer.global_alert is not None:
                global_alerts.append(importer.global_alert)

        test_match = g.config.get("test_match")

        def get_month_max_day(year, month):
            if month == 12:
                new_year = year + 1
                new_month = 1
            else:
                new_year = year
                new_month = month + 1
            return (ct_datetime(new_year, new_month) - HH).day

        return {
            "current_user": g.user,
            "global_alerts": global_alerts,
            "is_test": False if test_match is None else test_match in request.host,
            "test_css": g.config.get("test_css"),
            "get_month_max_day": get_month_max_day,
        }

    @app.teardown_request
    def shutdown_session(exception=None):
        if getattr(g, "sess", None) is not None:
            g.sess.close()

    @app.template_filter("date_format")
    def date_format_filter(dt, fmt="hh_res"):
        return date_format(dt, ongoing_str="Ongoing", fmt=fmt)

    @app.template_filter("now_if_none")
    def now_if_none(dt):
        return utc_datetime_now() if dt is None else dt

    @app.template_filter("to_ct")
    def to_ct_filter(dt):
        return to_ct(dt)

    @app.template_filter("dumps")
    def dumps_filter(d):
        return dumps(d)

    @app.template_filter("markdown")
    def markdown_filter(txt):
        md = MarkdownIt()
        return Markup(md.render(txt))

    return app


__version__ = version("chellow")
