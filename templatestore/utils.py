import base64
import datetime
from dateutil.relativedelta import relativedelta
import pytz
import re
import urllib.parse
import requests

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

def get_template_data_from_vendor(template_request):
    
    if template_request['vendor'] == 'GUPSHUP':
        

        url = "https://wamedia.smsgupshup.com/GatewayAPI/rest"

        # Request parameters (data to be sent in the POST request)
        params = {
            "method": "get_whatsapp_hsm",
            "userid": template_request['userid'],
            "password": template_request['password'],
            "limit": "2000",
            "name": template_request['template_name'],
            "fields": "%5B%22buttons%22%2C%22previouscategory%22%5D",
        }

        response = requests.get(url, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            json_response = response.json()
            print(json_response)
            return json_response
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
    
    else:
        return {"status": "failed", "reason": "vendor not found"}
