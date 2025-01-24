import json
import traceback

#HW02用的函式
import re
import requests # type: ignore

from model_configurations import get_model_configuration

from langchain_openai import AzureChatOpenAI # type: ignore
from langchain_core.messages import HumanMessage, SystemMessage # type: ignore


gpt_chat_version = 'gpt-4o'
gpt_config = get_model_configuration(gpt_chat_version)

i_llm = None
def use_llm():
    global i_llm
    if not i_llm:
        i_llm = AzureChatOpenAI(
                model=gpt_config['model_name'],
                deployment_name=gpt_config['deployment_name'],
                openai_api_key=gpt_config['api_key'],
                openai_api_version=gpt_config['api_version'],
                azure_endpoint=gpt_config['api_base'],
                temperature=gpt_config['temperature']
        )
    return i_llm

def get_prompt_template():
    return """
    你是使用繁體中文的台灣人，請回答中華民國台灣特定月份的紀念日有哪些，每一筆資料均以 LIST 方式按照以下指定的 JSON 格式呈現:
    {
     "Result": [
         {
             "date": "2024-10-10",
             "name": "中華民國國慶日"
         }
     ]
    }
    """

def generate_hw01(question):
    try:
        llm = use_llm()
        prompt_template = get_prompt_template()
        messages = [
            {"role": "system", "content": prompt_template},
            {"role": "user", "content": question}
        ]
        response = llm.invoke(messages)
        
        # Assuming the response is a JSON string
        response_content = response.content
        try:
            response = json.loads(response_content)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            response = {"Result": []}
        return json.dumps(response, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"An error occurred: {traceback.format_exc()}")
        return {"Result": []}

#HW 02用的函式

def translate_to_chinese(english_text):
    llm = use_llm()
    prompt = f"Translate the following holiday name to Traditional Chinese: {english_text}"
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    return response.content.strip()

def get_memorial_days(year, month):
    """Check the memorial days in a month."""
    try:
        api_key = 'P0djpVM0n9Mds3bGCuaizmWhbkXOuGcJ'  # Replace with your actual API key
        url = "https://calendarific.com/api/v2/holidays?&api_key={}&country=TW&year={}&month={}".format(api_key, year, month)
        resp = requests.get(url)
        
        if resp.status_code == 200:
            data = resp.json()
            holidays = data.get("response", {}).get("holidays", [])
            result = []
            for holiday in holidays:
                english_name = holiday["name_local"] if "name_local" in holiday else holiday["name"]
                chinese_name = translate_to_chinese(english_name)
                result.append({
                    "date": holiday["date"]["iso"],
                    "name": chinese_name
            })
            return {"Result": result}
        else:
            return {"Result": [], "error": "Failed to fetch data from API"}
    except Exception as e:
        return {"Result": [], "error": str(e)}

def generate_hw02(question):
    try:
        # Extract year and month from the question
        match = re.search(r'(\d{4})年台灣(\d{1,2})月', question)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            # Call the get_memorial_days function
            result = get_memorial_days(year, month)
            return json.dumps(result, ensure_ascii=False, indent=4)
        else:
            return json.dumps({"Result": [], "error": "Invalid question format"}, ensure_ascii=False, indent=4)
    except Exception as e:
        return json.dumps({"Result": [], "error": str(e)}, ensure_ascii=False, indent=4)
#    pass
        
def generate_hw03(question2, question3):
    pass
    
def generate_hw04(question):
    pass
    
def demo(question):
    llm = AzureChatOpenAI(
            model=gpt_config['model_name'],
            deployment_name=gpt_config['deployment_name'],
            openai_api_key=gpt_config['api_key'],
            openai_api_version=gpt_config['api_version'],
            azure_endpoint=gpt_config['api_base'],
            temperature=gpt_config['temperature']
    )
    message = HumanMessage(content=question)
    response = llm.invoke([message])
    
    return response
#    pass

# Test the function
question = "2024年台灣10月紀念日有哪些?"
response = generate_hw02(question)
print(response)
