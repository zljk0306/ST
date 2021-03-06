from sanic.response import html, json
from yhklibs.web.prosanic.template import render_template
from web.handler.base import st_member_blueprint
from web.auth import login_required


@st_member_blueprint.route("/index", methods=["GET"])
@login_required
async def index(request):
    actor = request["session"]["st_token"]
    return html(await render_template('/member/index.html', request=request, username=actor.get('username', '')))


@st_member_blueprint.route("/workbench", methods=["GET"])
@login_required
async def workbench(request):
    return html(await render_template('/member/workbench.html', request=request))
