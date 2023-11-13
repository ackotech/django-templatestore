import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example.settings")
django.setup()

"""
Steps to run the script:
1. Add templates list in TEMPLATES
2. Add DESTINATION(PROD) DB details in default(https://github.com/ackotech/django-templatestore/blob/451e05893e13f8d3b984433b76b7224937ceeb61/example/settings.py#L74)
3. Add SOURCE DB(ACKODEV) DB details after this line(https://github.com/ackotech/django-templatestore/blob/451e05893e13f8d3b984433b76b7224937ceeb61/example/settings.py#L81)
    "uat": {"ENGINE":"django.db.backends.postgresql","NAME":"ackodev_templates","USER":"ackodev_templates_rw_v1","PASSWORD":"","HOST":"acko-services-dev-rds.acko.in","PORT":""}
4. Update uat DB password.
5. Run the script
"""


SOURCE_DB = "uat"

from templatestore.models import *

TEMPLATES = []

# TODO Please update this mapping if there are any additions in the template_subtemplate table
UAT_TO_PROD_SUBTEMPLATE_ID_MAPPING = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 6,
    6: 8,
    7: 9,
    8: 10,
    9: 11,
    10: 14,
    11: 15,
    12: 16,
    13: 12,
    14: 13,
}


def clone_template(template_name):
    template = Template.objects.using(SOURCE_DB).filter(name=template_name).first()

    print(template.name)

    TEMPLATE = {
        "name": template.name,
        "type": template.type,
        "attributes": template.attributes,
        "created_by": template.created_by,
        "user_email": template.user_email,
    }

    t = Template.objects.create(**TEMPLATE)

    versions = (
        TemplateVersion.objects.using(SOURCE_DB)
        .filter(template_id=template)
        .order_by("created_on")
    )

    for version in versions:
        VERSION = {
            "template_id_id": t.id,
            "version": version.version,
            "sample_context_data": version.sample_context_data,
            "version_alias": version.version_alias,
            "created_by": version.created_by,
            "user_email": version.user_email,
            "tiny_url": version.tiny_url,
        }
        print(VERSION)
        v = TemplateVersion.objects.create(**VERSION)

        if template.default_version_id and version.id == template.default_version_id:
            t.default_version_id = v.id
            t.save()

        sub_templates = (
            SubTemplate.objects.using(SOURCE_DB)
            .filter(template_version_id=version.id)
            .all()
        )
        for sub_template in sub_templates:
            SUB_TEMPLATE = {
                "template_version_id_id": v.id,
                # TODO template_template_config are different in uat and prod databases
                "config_id": UAT_TO_PROD_SUBTEMPLATE_ID_MAPPING.get(
                    sub_template.config_id
                ),
                "data": sub_template.data,
            }

            SubTemplate.objects.create(**SUB_TEMPLATE)


if __name__ == "__main__":
    for name in TEMPLATES:
        clone_template(name)
        print("template cloned: ", name)
