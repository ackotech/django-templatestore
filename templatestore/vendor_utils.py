# views.py

from django.http import JsonResponse
import aiohttp
import asyncio
import json

import boto3

async def async_multiple_api_calls_view():
    # Define a list of URLs to call
    api_urls = [
        "https://wamedia.smsgupshup.com/GatewayAPI/rest",
        "https://wamedia.smsgupshup.com/GatewayAPI/rest",
        "https://wamedia.smsgupshup.com/GatewayAPI/rest",
        # Add more URLs as needed
    ]

    userid = "2000184968"
    password = 'TgqaruTx'
    template_name = 'test_all_buttons_1'
    # Query parameters corresponding to each URL (could be the same or different)
    query_params = [
        {
            "method": "get_whatsapp_hsm",
            "userid": userid,
            "password": password,
            "limit": "2000",
            "name": template_name,
            "fields": "%5B%22buttons%22%2C%22previouscategory%22%5D",
        },
        {
            "method": "get_whatsapp_hsm",
            "userid": userid,
            "password": password,
            "limit": "2000",
            "name": template_name,
            "fields": "%5B%22buttons%22%2C%22previouscategory%22%5D",
        },
        {
            "method": "get_whatsapp_hsm",
            "userid": userid,
            "password": password,
            "limit": "2000",
            "name": template_name,
            "fields": "%5B%22buttons%22%2C%22previouscategory%22%5D",
        },
        # Add more parameters as needed
    ]

    async with aiohttp.ClientSession() as session:
        # Create a list of coroutines (tasks) for each API call
        tasks = [client.get(url, params=params) for url, params in zip(api_urls, query_params)]

        # Run the tasks concurrently and wait for all of them to finish
        responses = await asyncio.gather(*tasks)

    # Process the responses
    results = []
    for response in responses:
        async with response:
            if response.status == 200:
                data = await response.json()
                results.append(data)
            else:
                results.append({"error": f"Failed to fetch {response.url}", "status": response.status})

    # Return the combined results as a JSON response
    print(result)
    return JsonResponse({"results": results})


def send_message(message_body, message_attributes=None):
    """
    Send a message to an Amazon SQS queue.

    :param queue: The queue that receives the message.
    :param message_body: The body text of the message.
    :param message_attributes: Custom attributes of the message. These are key-value
                               pairs that can be whatever you want.
    :return: The response from SQS that contains the assigned message ID.
    """

    # Create a session using the specified profile
    # session = boto3.Session(profile_name="ackodev")
    
    # Create an SQS client using the session
    # sqs = session.client('sqs')
    sqs = boto3.client('sqs')

    # sqs = boto3.client('sqs', region_name='ap-south-1')
    queue_url = "https://sqs.ap-south-1.amazonaws.com/663498825379/platform-ackommunication-email-p2"
    queue_url = "https://sqs.ap-south-1.amazonaws.com/663498825379/central-growth-template-update-sync"
    
    message_body = {"test": "abc"}

    if not message_attributes:
        message_attributes = {}

    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body), 
            MessageAttributes=message_attributes
        )
    except Exception as error:
        print("Send message failed: %s", message_body)
        raise error
    else:
        print(response)
        return response
