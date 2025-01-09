import os
from pathlib import Path
 
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat.completion_create_params import ResponseFormat

# Get the directory containing this file
current_dir = Path(__file__).parent
# Load the .env file from the same directory as this script
load_dotenv(current_dir / '.env',override=True)

#openai 1.0.0版本之后都推荐使用client方式访问api
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
#国内访问openai域名必须要走代理，这个是现成的一个反向代理
client.base_url = os.getenv("OPENAI_API_BASE")


def load_raiseconversation(question):
    msg = [{"role": "system", 
                "content": "As an AI-powered praise robot, my purpose is to uplift and motivate you. Share your recent achievements with me, and I will provide heartfelt compliments, insightful encouragement, and confidence-boosting messages. Together, we will celebrate your current efforts, reinforce your determination, and inspire you to continue working hard. Answer in Chinese."
}]
    msg.append({"role": "user", "content": question})
    return msg

# Send a request to the API and get a response
def get_response(msg,isJson = False):
    if isJson:
        response_format = {"type": "json_object"}
    else:
        response_format = {"type": "text"}
    try:
        completion = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=msg,
            response_format=response_format,
            max_tokens=4096,
            n=1,
            temperature=0.0
        )
        
        if hasattr(completion, 'choices'):
            return completion.choices[0].message.content
        elif isinstance(completion, str):
            # If we got a string response, try to parse it as JSON
            try:
                response_data = json.loads(completion)
                return response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
            except json.JSONDecodeError:
                return completion
    except Exception as e:
        print(f"Error: {e}")
        return None

# a = load_raiseconversation("你好")
# a = get_response(a)
# print(a)