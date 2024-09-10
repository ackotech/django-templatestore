import json
import logging
import re
import time
import uuid
import requests

from templatestore import app_settings
from templatestore.app_settings import GUPSHUP_WA_CREDENTIAL_LOB_MAP, ROBO_EMAIL
from templatestore.models import TemplateConfig, Template, TemplateVersion, SubTemplate, TemplateServiceProvider
from templatestore.utils import base64encode
from templatestore import app_settings as ts_settings

logger = logging.getLogger(__name__)


def transform_gupshup_request(data):
    if data['vendor'] == "GUPSHUP" and data['channel'] == "WHATSAPP":
        event_list = data['data']
        for template_event in event_list:
            """
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
            """
            template_detail = {
                "user_id": template_event['account'],
                "name": template_event['message_template_name']
            }
            result = get_whatsapp_gupshup_template(template_detail)
            logger.info(f"Got template details -> {result}")
            result = result['data'][0]
            # Convert request
            create_template_request = {
                'name': result['name'],
                'type': 'whatsapp',
                'version_alias': '',
                'tiny_url': [],
                'sub_templates': [],
                'sample_context_data': {}
            }

            variable_count = 0
            if "body" in result:
                matches = re.findall(r"\{\{\d+}}", result['body'])
                variable_count = len(matches)
            for i in range(0, variable_count):
                create_template_request['sample_context_data'][str(i)] = "sample"

            create_template_request['sub_templates'].append({
                'render_mode': "text",
                'sub_type': "textpart",
                'data': base64encode(result['body']) if "body" in result else ""
            })
            create_template_request['sub_templates'].append({
                'render_mode': "text",
                'sub_type': "header",
                'data': base64encode(result['header']) if "header" in result else ""
            })
            create_template_request['sub_templates'].append({
                'render_mode': "text",
                'sub_type': "footer",
                'data': base64encode(result['footer']) if "footer" in result else ""
            })

            dynamic_url_button_count = 1
            # Get button details
            if result["button_type"] != "NONE":
                buttons = {'buttons': []}
                for button in result['buttons']:
                    if button['type'] == 'PHONE_NUMBER':
                        buttons['buttons'].append({
                            "id": str(uuid.uuid4()),
                            "type": "phone_number",
                            "text": button["text"],
                            "phone_number": button["phone_number"]
                        })
                    elif button['type'] == 'URL' and button["urlType"] == "STATIC":
                        buttons['buttons'].append({
                            "id": str(uuid.uuid4()),
                            "type": "url",
                            "text": button["text"],
                            "urlType": "STATIC",
                            "url": button['url']
                        })
                    elif button['type'] == 'URL' and button["urlType"] == "DYNAMIC":
                        buttons['buttons'].append({
                            "id": str(uuid.uuid4()),
                            "type": "url",
                            "text": button['text'],
                            "urlType": "DYNAMIC",
                            "url": button['url'].replace("{{1}}", ""),
                            "dynamicUrlParam": "{{dynamic_url_param_" + str(dynamic_url_button_count) + "}}"
                        })
                        create_template_request['sample_context_data'][
                            f"dynamic_url_param_{dynamic_url_button_count}"] = "sample"
                        dynamic_url_button_count += 1

                    elif button['type'] == "QUICK_REPLY":
                        buttons['buttons'].append({
                            "type": "reply",
                            "reply": {
                                "id": str(uuid.uuid4()),
                                "title": button['text']
                            }
                        })

                create_template_request['sub_templates'].append({
                    'render_mode': "hybrid",
                    'sub_type': "button",
                    'data': base64encode(json.dumps(buttons))
                })

            create_template_request['attributes'] = GUPSHUP_WA_CREDENTIAL_LOB_MAP[str(template_event['account'])]
            create_template_request['version_alias'] = "auto_sync_" + str(int(time.time()))

            logger.info(f"Converted create template request -> {create_template_request}")

            res = save_template(create_template_request, user_email=ROBO_EMAIL)
            logger.info(f"Save Template Response for Auto Save -> {res}")
            default_req = {
                "name": create_template_request["name"],
                "version": res['version'],
                "default": True
            }
            default_res = make_template_default(default_req, user_email=ROBO_EMAIL)
            logger.info(f"Created default request -> {default_res}")
            return default_res

def get_whatsapp_gupshup_template(template_detail):
    params = {
        'method': 'get_whatsapp_hsm',
        'fields': "%5B%22buttons%22%2C%22previouscategory%22%5D",
        'userid': str(template_detail['user_id'])
    }
    if 'limit' in template_detail:
        params['limit'] = template_detail['limit']
    if 'name' in template_detail:
        params['name'] = template_detail['name']

    for credential in app_settings.GUPSHUP_WA_CREDENTIAL:
        if credential['user_id'] == str(template_detail['user_id']):
            params['password'] = credential['password']
            break

    response = requests.get(app_settings.GUPSHUP_WA_TEMPLATE_SYNC, params=params)
    data = {}
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Successful fetch template {data}")

    else:
        print(f"Error fetching data for template {params}")

    return data


def save_template(data, user_email):
    logging.info(f"Saving Template with data -> {data}")
    required_fields = {
        "name",
        "type",
        "sub_templates",
        "sample_context_data",
    }
    missing_fields = required_fields.difference(set(data.keys()))
    if len(missing_fields):
        raise (
            Exception(
                "Validation: missing fields `" + str(missing_fields) + "`"
            )
        )

    if not re.match("(^[a-zA-Z]+[a-zA-Z0-9_]*$)", data["name"]):
        raise (
            Exception(
                "Validation: `"
                + data["name"]
                + "` is not a valid template name"
            )
        )

    invalid_data = set()
    empty_data = set()

    for sub_template in data["sub_templates"]:
        if not re.match(
                "(^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$)",
                sub_template["data"],
        ):
            invalid_data.add(sub_template["sub_type"])

        if not sub_template["data"]:
            empty_data.add(sub_template["sub_type"])

    if len(invalid_data):
        raise (
            Exception(
                "Validation: `"
                + str(invalid_data)
                + "` data is not base64 encoded"
            )
        )

    cfgs = TemplateConfig.objects.filter(type=data["type"])
    # print(cfgs)
    if not len(cfgs):
        raise (
            Exception("Validation: `" + data["type"] + "` is not a valid type")
        )

    sub_types = {cfg.sub_type: cfg for cfg in cfgs}
    # print(sub_types)
    if len(empty_data) == len(sub_types):
        raise (
            Exception(
                "Validation: Atleast one of the sub_types `"
                + str(empty_data)
                + "` must be non empty"
            )
        )
    invalid_subtypes = set(
        [s["sub_type"] for s in data["sub_templates"]]
    ).difference(set(sub_types.keys()))
    if len(invalid_subtypes):
        raise (
            Exception(
                "Validation: invalid subtypes `"
                + str(invalid_subtypes)
                + "` for type `"
                + data["type"]
                + "`"
            )
        )

    diff_keys = set(sub_types.keys()).difference(
        set([s["sub_type"] for s in data["sub_templates"]])
    )
    if len(diff_keys):
        for sub_type in diff_keys:
            optional_field = TemplateConfig.objects.filter(sub_type=sub_type).values()[0]['optional']
            print("@@@@@", optional_field)
            # optional = obj.values('optional')
            if not optional_field:
                raise (
                    Exception(
                        "Validation: missing `"
                        + str(diff_keys)
                        + "` for type `"
                        + data["type"]
                        + "`"
                    )
                )

    if not len(data["sample_context_data"]):
        raise (
            Exception("Validation: sample_context_data field can not be empty")
        )

    if not re.match("(^[_a-zA-Z0-9 ]*$)", data.get("version_alias", "")):
        raise (
            Exception(
                "Validation: version_alias must contain only alphanumeric and space and underscore characters"
            )
        )

    templates = Template.objects.filter(name=data["name"])
    if not len(templates):
        if "attributes" not in data:
            raise (Exception("Validation: missing field `attributes`"))

        if not len(data["attributes"]):
            raise (Exception("Validation: attributes field can not be empty"))

        mandatory_attributes = {
            **cfgs[0].attributes,
            **ts_settings.TE_TEMPLATE_ATTRIBUTES,
        }

        missing_mandatory_attributes = set(
            mandatory_attributes.keys()
        ).difference(set(data["attributes"].keys()))

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

        tmp = Template.objects.create(
            name=data["name"],
            attributes=data["attributes"],
            type=data["type"],
            user_email=user_email,
        )
        tmp.save()

        version = "0.1"
        template = tmp

    else:
        if data["type"] != templates[0].type:
            raise (
                Exception(
                    "Validation: Template with name `"
                    + data["name"]
                    + "` already exists with type `"
                    + templates[0].type
                    + "`"
                )
            )

        template = templates[0]  # only one template should exist
        max_version = TemplateVersion.objects.filter(
            template_id=template
        ).order_by("-id")[:1]

        major_version, minor_version = max_version[0].version.split(".")
        minor_version = str(int(minor_version) + 1)
        version = major_version + "." + minor_version

    tmp_ver = TemplateVersion.objects.create(
        template_id=template,
        version=version,
        sample_context_data=data["sample_context_data"],
        version_alias=data["version_alias"] if "version_alias" in data else "",
        user_email=user_email,
        tiny_url=data["tiny_url"],
    )
    tmp_ver.save()
    for sub_tmp in data["sub_templates"]:
        print(sub_tmp)
        st = SubTemplate.objects.create(
            template_version_id=tmp_ver,
            config=TemplateConfig.objects.get(
                type=data["type"],
                sub_type=sub_tmp["sub_type"],
                render_mode=sub_tmp["render_mode"],
            ),
            data=sub_tmp["data"],
        )
        print(st)
        st.save()

    template_data = {
        "name": data["name"],
        "version": version,
        "default": False,
        "attributes": template.attributes,
    }
    return template_data


def make_template_default(data, user_email):
    try:
        tmp = Template.objects.get(name=data['name'])
    except Exception:
        raise (Exception("Validation: Template with given name does not exist"))

    max_version = TemplateVersion.objects.filter(template_id=tmp).order_by(
        "-id"
    )[:1]

    major_version, minor_version = max_version[0].version.split(".")
    new_version = str(float(major_version) + 1)

    try:
        tmp_ver = TemplateVersion.objects.get(
            template_id=tmp.id, version=data['version']
        )
    except Exception:
        raise (
            Exception(
                "Validation: Template with given name and version does not exist"
            )
        )

    sts = SubTemplate.objects.filter(template_version_id=tmp_ver.id)

    tmp_ver_new = TemplateVersion.objects.create(
        template_id=tmp,
        version=new_version,
        sample_context_data=tmp_ver.sample_context_data,
        version_alias=tmp_ver.version_alias,
        user_email=user_email,
    )
    tmp_ver_new.save()

    for st in sts:
        SubTemplate.objects.create(
            template_version_id=tmp_ver_new, config=st.config, data=st.data
        ).save()
    tmp.default_version_id = tmp_ver_new.id
    tmp.save(update_fields=["default_version_id", "modified_on"])

    template_data = {
        "name": tmp.name,
        "version": tmp_ver_new.version,
        "default": True if tmp.default_version_id == tmp_ver_new.id else False,
        "attributes": tmp.attributes,
    }
    return template_data

def save_vendor_info(data):
    tmp = TemplateServiceProvider.objects.create(
        vendor=data['vendor'],
        channel=data['channel'],
        account_id=data['account_id'],
        is_active=True
    )
    tmp.save()
    data["is_active"] = tmp.is_active
    data['created_on'] = tmp.created_on
    data['modified_on'] = tmp.modified_on
    return data


def get_vendor_info():
    ts = TemplateServiceProvider().get_all_objects()

    res = {"data": []}
    for t in ts:
        res["data"].append({
            "id": t.id,
            "vendor": t.vendor,
            "channel": t.channel,
            "account_id": t.account_id,
            "is_active": t.is_active
        })
    return res