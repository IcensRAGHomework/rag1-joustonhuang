import json
import traceback

#HW02用的函式
import re
import requests # type: ignore
from model_configurations import get_model_configuration
from langchain_openai import AzureChatOpenAI # type: ignore

#HW03用的函式
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage # type: ignore
from langchain_core.runnables.history import RunnableWithMessageHistory # type: ignore
from langchain_community.chat_message_histories import ChatMessageHistory # type: ignore
from langchain_core.chat_history import BaseChatMessageHistory # type: ignore
# from langchain_core.agents import create_openai_functions_agent # type: ignore

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
                    "name": chinese_name.split("is translated to Traditional Chinese as ")[-1]
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
    new_holiday = json.loads(question3)
    prompt_template = get_prompt_template()
    store = {}
    history = ChatMessageHistory()
    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        if session_id not in store:
            store[session_id] = ChatMessageHistory()
        return store.get(session_id, ChatMessageHistory())
    tools = ()  # Define your tools here if any
    model = use_llm()  # Define your model
    # Mock executor for example purposes
    class MockExecutor:
        def with_listeners(self, on_end):
            return self
        def with_alisteners(self, on_end):
            return self
        def invoke(self, input):
            return input
    agent_executor = MockExecutor()
    agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor.with_listeners(on_end=None).with_alisteners(on_end=None),
        get_session_history,
        input_key="input",
        history_key="chat_history",
    )
    try:
        # Extract year and month from the question2
        match2 = re.search(r'(\d{4})年台灣(\d{1,2})月', question2)
        if match2:
            year = int(match2.group(1))
            month = int(match2.group(2))
            # Create a RunnableWithMessageHistory to store the previous result
            previous_result = json.loads(generate_hw02(question2))
            previous_holidays = [holiday["name"] for holiday in previous_result["Result"]]

            # Extract date and name from question3
            new_holiday = json.loads(question3[question3.find('{'):])
            if new_holiday["name"] not in previous_holidays:
                add = True
                reason = f'{new_holiday["name"]}並未包含在{month}月的節日清單中。目前{month}月的現有節日包括{", ".join(previous_holidays)}。因此，如果該日被認定為節日，應該將其新增至清單中。'
            else:
                add = False
                reason = f'{new_holiday["name"]}已包含在{month}月的節日清單中。'
            
            return json.dumps({"Result": [{"add": add, "reason": reason}]}, ensure_ascii=False, indent=4)
        else:
            return json.dumps({"Result": [{"add": False, "reason": "Invalid question format for question2"}]}, ensure_ascii=False, indent=4)
    except Exception as e:
        return json.dumps({"Result": [{"add": add, "reason": reason}]}, ensure_ascii=False, indent=4)
#    pass
    
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

#print(f"作業1答案...")
#response = generate_hw01(question)
#print(response)

#print(f"作業2答案...")
#response = generate_hw02(question)
#print(response)

question2 = "2024年台灣10月紀念日有哪些?"
question3 = '{"date": "10-31", "name": "蔣公誕辰紀念日"}'
result_hw02 = generate_hw02(question2)
#print(f"作業2結果: {result_hw02}")
print(f"作業3答案...")
response = generate_hw03(question2, question3)
print(response)

#print(f"作業4答案...")
#question = "請問中華台北的積分是多少"
#response = generate_hw04(question)
