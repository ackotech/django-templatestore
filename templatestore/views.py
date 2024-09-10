from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from datetime import datetime
import json
import re
import logging
import requests
from templatestore.models import Template, TemplateVersion, SubTemplate, TemplateConfig, TemplateServiceProvider
from templatestore.template_utils import transform_gupshup_request, save_template, make_template_default, \
    save_vendor_info, get_vendor_info, get_whatsapp_gupshup_template
from templatestore.utils import (
    base64decode,
    base64encode,
    generatePayload,
)
from templatestore import app_settings as ts_settings
from django.db import connection

logger = logging.getLogger(__name__)
PDF_URL = ts_settings.WKPDFGEN_SERVICE_URL
PDF_ASSET_URL = ts_settings.WKPDFGEN_ASSET_URL
TINY_URL = ts_settings.TINY_URL
QUERY = ts_settings.QUERY


def index(request):
    export_settings = {
        "TE_TEMPLATE_ATTRIBUTES": ts_settings.TE_TEMPLATE_ATTRIBUTES,
        "TE_BASEPATH": ts_settings.TE_BASEPATH,
    }
    return render(
        request, "index.html", context={"settings": json.dumps(export_settings)}
    )


def render_via_jinja(template, context):
    from jinja2 import Template

    return base64encode(Template(base64decode(template)).render(context))


@csrf_exempt
def render_pdf(request):
    # log requests
    if request.method != "POST":
        return HttpResponseBadRequest("invalid request method: " + request.method)

    try:
        data = json.loads(request.body)
        template = data["template"]
        context = data["context"]
        context["base_path"] = PDF_ASSET_URL
        rendered_html_template = render_via_jinja(template, context)
        pdf = requests.post(
            PDF_URL + "/render_pdf/",
            data=json.dumps({"html": str(base64decode(rendered_html_template))}),
        )
        return HttpResponse(pdf, content_type="application/pdf")

    except Exception as e:
        logger.exception(e)

        return HttpResponse(
            json.dumps({"message": str(e)}),
            content_type="application/json",
            status=500,
        )


@csrf_exempt
def render_template_view(request):
    # log requests
    if request.method != "POST":
        return HttpResponseBadRequest("invalid request method: " + request.method)

    try:
        data = json.loads(request.body)
        required_fields = {"template", "context", "handler"}
        missing_fields = required_fields.difference(set(data.keys()))

        if len(missing_fields):
            raise (
                Exception("Validation: missing fields `" + str(missing_fields) + "`")
            )

        template = data["template"]
        context = data["context"]
        handler = data["handler"]
        if not re.match(
            "(^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$)", template
        ):
            raise (Exception("Validation: Template data is not base64 encoded"))

        if handler == "jinja2":
            rendered_template = render_via_jinja(template, context)
            data = {
                "rendered_template": rendered_template,
                "rendered_on": datetime.now(),
            }
            return JsonResponse(data, safe=False)

        else:
            raise Exception("Invalid Template Handler: %s", handler)

    except Exception as e:
        logger.exception(e)

        return HttpResponse(
            json.dumps({"message": str(e)}),
            content_type="application/json",
            status=400,
        )


@csrf_exempt
def get_templates_view_v2(request):
    if request.method == "GET":
        try:
            cursor = connection.cursor()
            cursor.execute(QUERY)
            rows = cursor.fetchall()
            template_list = []
            for row in rows:
                obj = {
                    "name": row[0],
                    "version": row[1],
                    "default": True if row[2] != None else False,
                    "type": row[3],
                    "attributes": row[4],
                    "created_on": row[5],
                    "modified_on": row[6],
                    "created_by": row[7],
                }
                template_list.append(obj)
            return JsonResponse(template_list, safe=False)

        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                json.dumps({"message": str(e)}),
                content_type="application/json",
                status=400,
            )

    else:
        return HttpResponse(
            json.dumps({"message": "no method found"}),
            content_type="application/json",
            status=404,
        )


@csrf_exempt
def get_templates_view(request):
    if request.method == "GET":
        try:
            offset = int(request.GET.get("offset", 0))
            limit = int(request.GET.get("limit", ts_settings.TE_ROWLIMIT))

            templates = Template.objects.all().order_by("-modified_on")[
                offset : offset + limit
            ]
            template_list = [
                {
                    "name": t.name,
                    "version": TemplateVersion.objects.get(
                        pk=t.default_version_id
                    ).version
                    if t.default_version_id
                    else "0.1",
                    "default": True if t.default_version_id else False,
                    "type": t.type,
                    "attributes": t.attributes,
                    "created_on": t.created_on,
                    "modified_on": t.modified_on,
                    "created_by": t.user_email,
                }
                for t in templates
            ]

            return JsonResponse(template_list, safe=False)

        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                json.dumps({"message": str(e)}),
                content_type="application/json",
                status=400,
            )

    else:
        return HttpResponse(
            json.dumps({"message": "no method found"}),
            content_type="application/json",
            status=404,
        )


@csrf_exempt
@transaction.atomic
def post_template_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_email = request.POST.get("email")
            template_data = save_template(data, user_email)
            return JsonResponse(template_data, status=201)
        except Exception as e:
            logger.exception(e)

            return HttpResponse(
                json.dumps({"message": str(e)}),
                content_type="application/json",
                status=400,
            )

    else:
        return HttpResponse(
            json.dumps({"message": "no method found"}),
            content_type="application/json",
            status=404,
        )


@csrf_exempt
def get_template_versions_view(request, name):
    if request.method == "GET":
        try:
            offset = int(request.GET.get("offset", 0))
            limit = int(request.GET.get("limit", ts_settings.TE_ROWLIMIT))

            try:
                t = Template.objects.get(name=name)
            except Exception:
                raise (
                    Exception(
                        "Validation: Template with name `" + name + "` does not exist"
                    )
                )
            tvs = TemplateVersion.objects.filter(template_id=t.id).order_by("-id")[
                offset : offset + limit
            ]
            version_list = [
                {
                    "version": tv.version,
                    "default": True if t.default_version_id == tv.id else False,
                    "created_on": tv.created_on,
                    "version_alias": tv.version_alias,
                    "created_by": tv.user_email,
                }
                for tv in tvs
            ]
            return JsonResponse(version_list, safe=False)

        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                json.dumps({"message": str(e)}),
                content_type="application/json",
                status=400,
            )

    else:
        return HttpResponse(
            json.dumps({"message": "no method found"}),
            content_type="application/json",
            status=404,
        )


@csrf_exempt
def get_tiny_url(request, name, version):
    if request.method != "GET":
        return HttpResponseBadRequest("invalid request method: " + request.method)

    templateTable = Template.objects.filter(name=name)
    if len(templateTable) == 0:
        return HttpResponseBadRequest("Template Doesnot exists")

    versionTable = TemplateVersion.objects.filter(
        template_id_id=templateTable[0].id, version=version
    )
    if len(versionTable) == 0:
        return HttpResponseBadRequest("Corresponding version table doesnot exists")

    data = json.dumps(versionTable[0].tiny_url)
    return HttpResponse(data)


@csrf_exempt
def save_tiny_url(request):
    if request.method != "PUT":
        return HttpResponseBadRequest("invalid request method: " + request.method)

    data = json.loads(request.body)
    version = data["templateVersion"]
    name = data["templateName"]
    templateTable = Template.objects.filter(name=name)
    if len(templateTable) == 0:
        return HttpResponseBadRequest("Template Doesnot exists")

    versionTable = TemplateVersion.objects.filter(
        template_id_id=templateTable[0].id, version=version
    )
    if len(versionTable) == 0:
        return HttpResponseBadRequest(
            "No corresponding version table exists for :" + name + " table"
        )

    versionTable[0].tiny_url = data["tinyUrlArray"]

    try:
        versionTable[0].save()
    except Exception as e:
        logger.exception(e)
        return HttpResponse(
            json.dumps({"message": "Some unknown error occured"}),
            content_type="application/json",
            status=500,
        )
    return HttpResponse(
        json.dumps({"message": "Saved successfully"}),
        content_type="application/json",
        status=200,
    )


@csrf_exempt
def get_render_template_view(request, name, version=None):
    if request.method == "GET":
        try:
            data = json.loads(request.body)
            if "context_data" not in data:
                raise (Exception("Validation: context_data is missing"))

            try:
                t = Template.objects.get(name=name)
            except Exception:
                raise (
                    Exception(
                        "Validation: Template with name `" + name + "` does not exist"
                    )
                )
            if not version:
                try:
                    TemplateVersion.objects.get(id=t.default_version_id)
                except Exception:
                    raise (
                        Exception(
                            "Validation: No default version exists for the given template"
                        )
                    )
            tv = (
                TemplateVersion.objects.get(template_id=t.id, version=version)
                if version
                else TemplateVersion.objects.get(id=t.default_version_id)
            )
            try:
                listOfData = generatePayload(t, tv, data)
            except Exception as e:
                logger.exception(e)
                return HttpResponse(
                    json.dumps({"message": str(e)}),
                    content_type="application/json",
                    status=400,
                )

            i = 0
            while i < len(listOfData):
                url = TINY_URL + "/api/v1/create_tiny_url"
                result = requests.post(
                    url,
                    json.dumps(listOfData[i]),
                    headers={"content-type": "application/json"},
                )
                result = result.json()
                temp = (
                    "data['context_data']"
                    + tv.tiny_url[i]["urlKey"]
                    + "='"
                    + result["tiny_url"]
                    + "'"
                )
                exec(temp)
                i = i + 1

            stpls = SubTemplate.objects.filter(template_version_id=tv.id)
            try:
                res = {
                    "version": tv.version,
                    "type": t.type,
                    "attributes": t.attributes,
                    "sub_templates": [
                        {
                            "sub_type": stpl.config.sub_type,
                            "rendered_data": render_via_jinja(
                                stpl.data, data["context_data"]
                            ),
                        }
                        for stpl in stpls
                    ],
                }
            except Exception as e:
                logger.exception(e)
                return HttpResponse(
                    json.dumps({"Failed to render template due to ": str(e)}),
                    content_type="application/json",
                    status=400,
                )

            return JsonResponse(res, safe=False)
        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                json.dumps({"message": str(e)}),
                content_type="application/json",
                status=400,
            )

    else:
        return HttpResponse(
            json.dumps({"message": "no method found"}),
            content_type="application/json",
            status=404,
        )


@csrf_exempt
@transaction.atomic
def get_template_details_view(request, name, version):
    if request.method == "GET":
        try:

            try:
                t = Template.objects.get(name=name)
            except Exception:
                raise (Exception("Validation: Template with given name does not exist"))

            try:
                tv = TemplateVersion.objects.get(template_id=t.id, version=version)
            except Exception:
                raise (
                    Exception(
                        "Validation: Template with given name and version does not exist"
                    )
                )

            stpls = SubTemplate.objects.filter(template_version_id=tv.id)

            res = {
                "name": t.name,
                "version": tv.version,
                "type": t.type,
                "sub_templates": [
                    {
                        "sub_type": stpl.config.sub_type,
                        "data": stpl.data,
                        "render_mode": stpl.config.render_mode,
                    }
                    for stpl in stpls
                ],
                "default": True if t.default_version_id == tv.id else False,
                "attributes": t.attributes,
                "sample_context_data": tv.sample_context_data,
                "version_alias": tv.version_alias,
            }

            return JsonResponse(res, safe=False)
        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                json.dumps({"message": str(e)}),
                content_type="application/json",
                status=400,
            )

    elif request.method == "POST":
        try:
            data = json.loads(request.body)

            if not data.get("default", False):
                return HttpResponse(status=400)

            data['name'] = name
            data['version'] = version
            user_email = request.POST.get("email")

            template_data = make_template_default(data, user_email)
            return JsonResponse(template_data, status=200)

        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                json.dumps({"message": str(e)}),
                content_type="application/json",
                status=400,
            )
    else:
        return HttpResponse(
            json.dumps({"message": "no method found"}),
            content_type="application/json",
            status=404,
        )


@csrf_exempt
def get_config_view(request):
    if request.method == "GET":
        offset = int(request.GET.get("offset", 0))
        limit = int(request.GET.get("limit", ts_settings.TE_ROWLIMIT))
        try:
            ts = TemplateConfig.objects.all()[offset : offset + limit]

            tes = {}
            for t in ts:
                if t.type in tes:
                    tes[t.type]["sub_type"].append(
                        {"type": t.sub_type, "render_mode": t.render_mode}
                    )
                else:
                    tes[t.type] = {
                        "sub_type": [
                            {"type": t.sub_type, "render_mode": t.render_mode}
                        ],
                        "attributes": t.attributes,
                    }

            return JsonResponse(tes, safe=False)

        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                json.dumps({"message": str(e)}),
                content_type="application/json",
                status=404,
            )

    else:
        return HttpResponse(
            json.dumps({"message": "no method found"}),
            content_type="application/json",
            status=404,
        )


@csrf_exempt
def patch_attributes_view(request, name):
    if request.method == "PATCH":
        try:
            data = json.loads(request.body)

            if "attributes" not in data:
                raise (Exception("Validation: attributes are not provided"))

            try:
                template = Template.objects.get(name=name)
            except Exception as e:
                raise (Exception("Validation: Template with given name does not exist"))

            cfgs = TemplateConfig.objects.filter(type=template.type)

            mandatory_attributes = {
                **cfgs[0].attributes,
                **ts_settings.TE_TEMPLATE_ATTRIBUTES,
            }

            missing_mandatory_attributes = set(mandatory_attributes.keys()).difference(
                set(data["attributes"].keys())
            )

            if len(missing_mandatory_attributes):
                raise (
                    Exception(
                        "Validation: missing mandatory attributes `"
                        + str(missing_mandatory_attributes)
                        + "`"
                    )
                )

            invalid_valued_attributes = set(
                key
                for key in mandatory_attributes.keys()
                if "allowed_values" in mandatory_attributes[key]
                and data["attributes"][key]
                not in mandatory_attributes[key]["allowed_values"]
            )

            if len(invalid_valued_attributes):
                raise (
                    Exception(
                        "Validation: invalid values for the attributes `"
                        + str(invalid_valued_attributes)
                        + "`"
                    )
                )

            for key in data["attributes"]:
                if not isinstance(data["attributes"][key], str):
                    raise (
                        Exception(
                            "Validation: attributes must be a key value pair and value must be a string"
                        )
                    )

            template.attributes = data["attributes"]
            template.save(update_fields=["attributes", "modified_on"])
            data = {"name": name, "attributes": data["attributes"]}
            return JsonResponse(data, status=200)
        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                json.dumps({"message": str(e)}),
                content_type="application/json",
                status=400,
            )
    else:
        return HttpResponse(
            json.dumps({"message": "no method found"}),
            content_type="application/json",
            status=404,
        )


@csrf_exempt
def sync_template(request, vendor, channel):
    if request.method != "POST":
        return HttpResponse(
            json.dumps({"message": "no method found"}),
            content_type="application/json",
            status=404,
        )

    # Post Request Processing
    if vendor.lower() == "gupshup" and channel.lower() == "whatsapp":
        request_body = json.loads(request.body)
        """
        Request Body
        {
          "vendor": "GUPSHUP",
          "channel": "WHATSAPP",
          "data": [
            {
              "event_id": 5251693554363068000,
              "field": "message_template_status_update",
              "event": "ENABLED",
              "message_template_name": "test_webhook_1",
              "message_template_language": "en",
              "message_template_id": 7140758,
              "message_template_type": "TEXT",
              "account": 2000184968,
              "reason": "NONE",
              "time": 1725562284
            }
          ]
        }
        """
        try:
            response = transform_gupshup_request(request_body)
            return JsonResponse(response, status=200)
        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                json.dumps({"message": str(e)}),
                content_type="application/json",
                status=400,
            )
    else:
        return HttpResponse(
            json.dumps({"message": "no method found"}),
            content_type="application/json",
            status=404,
        )


@csrf_exempt
def vendor_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            if ("vendor" not in data) or ("channel" not in data) or ("account_id" not in data):
                return JsonResponse(json.dumps({"message": "required parameter missing"}), status=400)

            data = save_vendor_info(data)

            return JsonResponse(data, status=200)

        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                json.dumps({"message": str(e)}),
                content_type="application/json",
                status=500,
            )

    elif request.method == "GET":
        try:
            res = get_vendor_info()
            return JsonResponse(res, status=200)


        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                json.dumps({"message": str(e)}),
                content_type="application/json",
                status=404,
            )


@csrf_exempt
def get_vendor_template(request, vendor, channel):
    if request.method != "GET":
        return HttpResponse(
            json.dumps({"message": "no method found"}),
            content_type="application/json",
            status=404,
        )
    if request.GET.get("account_id") is None:
        return JsonResponse(
            {"message": "Account Id is required"},
            status=400,
        )
    account_id = request.GET.get("account_id")
    found_config = False
    res = get_vendor_info()
    for vendor_info in res['data']:
        if vendor.lower() == vendor_info['vendor'].lower() and channel.lower() == vendor_info['channel'].lower() and account_id.lower() == vendor_info['vendor'].lower():
            found_config = True
            break
    if not found_config:
        JsonResponse({"message": "vendor config not found"}, status=400)

    if vendor.lower() == "gupshup":
        template_detail = {
            'user_id': str(account_id)
        }
        if request.GET.get("template_name") is not None:
            template_detail['name'] = request.GET.get("template_name")
        if request.GET.get("limit") is not None:
            template_detail['limit'] = request.GET.get("limit")
        else:
            template_detail['limit'] = 10000
        data = get_whatsapp_gupshup_template(template_detail)

    return JsonResponse(data, status=200)
