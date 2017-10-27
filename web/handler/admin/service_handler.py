from sanic.response import html, json
from yhklibs.web.prosanic.template import render_template
from web.handler.base import st_admin_blueprint
from yhklibs.db.postgresql import yhk_session
from web.auth import admin_login_required
from web.models.service import Service, Package
from web.models.category import Category
from yhklibs import yhk_app


@st_admin_blueprint.route("/service", methods=["GET"])
@admin_login_required
async def index(request):
    return html(await render_template('/admin/service.html', request=request))


@st_admin_blueprint.route("/service/list", methods=["GET"])
@admin_login_required
async def get_service_list(request):
    offset = request.args.get("offset")
    limit = request.args.get("limit")
    service_name = request.args.get("service_name")
    if offset:
        offset = int(offset)
    if limit:
        limit = int(limit)
    with yhk_session() as session:
        data, total = await Service.query(session, service_name, offset, limit)
        items = []
        for item in data:
            service = item.to_json()
            service["category_name"] = item.category.category_name
            items.append(service)
        return json({"rows": items, "total": total})


@st_admin_blueprint.route("/service/<service_id:int>/view", methods=["GET"])
@admin_login_required
async def view(request, service_id):
    with yhk_session() as session:
        service = await Service.get(session, service_id)
        return html(await render_template('/admin/service_view.html', request=request, data=service))


@st_admin_blueprint.route("/service/<service_id:int>/delete", methods=["POST"])
@admin_login_required
async def delete_service(request, service_id):
    with yhk_session() as session:
        service = await Service.get(session, service_id)
        if not service:
            return json({"code": 500, "message": "删除失败，服务不存在！"})
        service.delete_flag = True
        session.commit()
    return json({"code": 200, "message": "删除成功！"})


@st_admin_blueprint.route("/service/edit", methods=["GET", "POST"])
@admin_login_required
async def service_edit(request):
    if request.method == "GET":
        service_id = request.args.get("service_id")
        task_tpls = yhk_app.config["TASK_TEMPLATES"]
        with yhk_session() as session:
            categories = await Category.get_all(session)

            if not service_id:
                return html(await render_template('/admin/service_edit.html', request=request, data=None,
                                                  categories=categories, task_tpls=task_tpls))
            else:
                service = await Service.get(session, service_id)
                service.packages = list(filter(lambda p: p.delete_flag is False, service.packages))
                return html(await render_template('/admin/service_edit.html', request=request, data=service,
                                                  categories=categories, task_tpls=task_tpls))
    elif request.method == "POST":
        service_id = request.form.get("service_id")
        service_name = request.form.get("service_name")
        sub_heading = request.form.get("sub_heading")
        price = request.form.get("price")
        enable = request.form.get("enable")
        category_id = request.form.get("category_id")
        order_no = request.form.get("order_no")
        remark = request.form.get("remark")
        instruction = request.form.get("instruction")
        task_tpl = request.form.get("task_tpl")

        if not (
                                    service_name and sub_heading and price and enable and category_id and order_no and instruction and task_tpl):
            return json({"code": 500, "message": "请填写完整信息！"})
        if service_id:
            service_id = int(service_id)
        category_id = int(category_id)
        order_no = int(order_no)
        price = float(price)
        enable = True if enable == "true" else False
        with yhk_session() as session:
            if not service_id:
                service = Service()
                session.add(service)
            else:
                service = await Service.get(session, service_id)
                if not service:
                    return json({"code": 4001, "message": "当前服务不存在！"})
            service.service_name = service_name
            service.sub_heading = sub_heading
            service.price = price
            service.enable = enable
            service.category_id = category_id
            service.order_no = order_no
            service.remark = remark
            service.instruction = instruction
            service.task_template_code = task_tpl
            session.commit()
            return json({"code": 200, "message": "保存成功！", "service_id": service.id})


@st_admin_blueprint.route("/service/package/save", methods=["POST"])
@admin_login_required
async def service_package_save(request):
    service_id = request.form.get("service_id")
    package_id = request.form.get("package_id")
    package_name = request.form.get("package_name")
    package_price = request.form.get("package_price")
    times = request.form.get("times")
    package_type = request.form.get("package_type")
    order_no = request.form.get("order_no")
    if not (service_id and package_name and package_price and times and package_type and order_no):
        return json({"code": 500, "message": "请填写完整信息！"})
    remark = request.form.get("remark")
    can_buy_again = request.form.get("can_buy_again")
    is_marked_price = request.form.get("is_marked_price")
    enable = request.form.get("enable")

    service_id = int(service_id)
    if package_id:
        package_id = int(package_id)
    package_price = float(package_price)
    times = int(times)
    package_type = int(package_type)
    order_no = int(order_no)
    can_buy_again = bool(can_buy_again)
    is_marked_price = bool(is_marked_price)
    enable = bool(enable)
    with yhk_session() as session:
        if not package_id:
            package = Package()
            package.service_id = service_id
            session.add(package)
        else:
            package = await Package.get(session, package_id)
            if not package:
                return json({"code": 4001, "message": "当前套餐不存在！"})
        package.package_name = package_name
        package.package_price = package_price
        package.times = times
        package.package_type = package_type
        package.remark = remark
        package.can_buy_again = can_buy_again
        package.is_marked_price = is_marked_price
        package.enable = enable
        package.order_no = order_no
        session.commit()
        return json({"code": 200, "message": "保存成功！", "package_id": package.id})


@st_admin_blueprint.route("/service/package/<package_id:int>/delete", methods=["POST"])
@admin_login_required
async def service_package_delete(request, package_id):
    with yhk_session() as session:
        package = await Package.get(session, package_id)
        if not package:
            return json({"code": 4001, "message": "当前套餐不存在！"})
        package.delete_flag = True
        session.commit()

    return json({"code": 200, "message": "删除成功！"})
