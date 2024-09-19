import base64
import datetime
from dateutil.relativedelta import relativedelta
import pytz
import re

regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def base64decode(template):
    output = base64.b64decode(template.encode("utf-8"))
    return str(output.decode("utf-8"))


def base64encode(rendered_output):
    output = base64.b64encode(rendered_output.encode("utf-8"))
    return str(output.decode("utf-8"))

def generateDate(days):
    # .isoformat()
    IST = pytz.timezone("Asia/Kolkata")
    dt = datetime.datetime.now(IST) + relativedelta(days=+days)
    return str(dt.isoformat())

def generatePayload(templateTable, versionTable, data):
    ans = []
    i = 0
    while i < len(versionTable.tiny_url):
        original_url = "data" + "['context_data']" + versionTable.tiny_url[i]["urlKey"]
        
        try:
            eval(original_url)
        except Exception as e:
            raise Exception("Key not found: "+versionTable.tiny_url[i]["urlKey"])

        try:
            if(re.match(regex, eval(original_url)) is None):
                raise Exception("Invalid URL "+eval(original_url))
        except Exception as e:
            raise e
        
        lob = templateTable.attributes["lob"]
        journey = templateTable.attributes["journey"]
        days = versionTable.tiny_url[i]["expiry"]
        expiry = generateDate(int(days))
        ans.append(
            {
                "original_url": eval(original_url),
                "lob": lob,
                "journey": journey,
                "expiry_time": expiry,
            }
        )
        i = i + 1
    return ans


def replace_placeholders(text):
    def replacement(match):
        # Extract the number from {{number}}
        number = match.group(1)
        return f"{{{{var{number}}}}}"  # return {{var<number>}}

    # Regular expression to find {{number}}
    replaced_text = re.sub(r"\{\{(\d+)\}\}", replacement, text)
    return replaced_text


def replace_sms_vars_with_placeholders(input_string):
    count = 1
    while '{#var#}' in input_string:
        input_string = input_string.replace('{#var#}', f'{{{{var{count}}}}}', 1)
        count += 1
    return input_string