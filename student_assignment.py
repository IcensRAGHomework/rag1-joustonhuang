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

#HW04用的函式
from PIL import Image, ImageEnhance, ImageFilter # type: ignore
import pytesseract # type: ignore
#from langchain import LangChain

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

# HW03需要的函式
def number_translate_to_chinese(english_text):
    llm = use_llm()
    prompt = f"Translate the number to Traditional Chinese: {english_text}. For example 10 translate to 十, 9 translate to 九. And please only output the Traditional Chinese number."
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    return response.content.strip()

def generate_hw03(question2, question3):
    new_holiday_json = question3[question3.find("{"):question3.rfind("}")+1]  # Extract the JSON part
    new_holiday = json.loads(new_holiday_json)
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
            previous_result = json.loads(generate_hw02(question))
            previous_holidays = [holiday["name"] for holiday in previous_result["Result"]]


            # Extract date and name from question3
            new_holiday_json = question3[question3.find("{"):question3.rfind("}")+1]  # Extract the JSON part
            new_holiday = json.loads(new_holiday_json)
            if new_holiday["name"] not in previous_holidays:
                add = True
                reason = f'{new_holiday["name"]}並未包含在{number_translate_to_chinese(str(month))}月的節日清單中。目前{number_translate_to_chinese(str(month))}月的現有節日包括{", ".join(previous_holidays)}。因此，如果該日被認定為節日，應該將其新增至清單中。'

            else:
                add = False
                reason = f'{new_holiday["name"]}已包含在{number_translate_to_chinese(str(month))}月的節日清單中。目前{number_translate_to_chinese(str(month))}月的現有節日包括{", ".join(previous_holidays)}。因此，不應該將其新增至清單中。'
            result_dict = {
                "Result": {
                    "add": add,
                    "reason": reason
                }
            }
            result_json = json.dumps(result_dict, ensure_ascii=False, indent=4)
            result_json = result_json.replace('{\n    "Result": {', '{\n    "Result":\n    {')
            return result_json
        else:
            return json.dumps({"Result": {"add": False, "reason": "Invalid question format for question2"}}, ensure_ascii=False, indent=4)
    except Exception as e:
        result_dict = {
            "Result": {
                "add": False,
                "reason": str(e)
            }
        }
        result_json = json.dumps(result_dict, ensure_ascii=False, indent=4)
        result_json = result_json.replace('{\n    "Result": {', '{\n    "Result":\n    {')
        return result_json
#    pass

# HW04需要的函式
def preprocess_image(image_path):
    image = Image.open(image_path)
    # Convert to grayscale
    image = image.convert('L')
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)
    # Apply a filter to remove noise
    image = image.filter(ImageFilter.MedianFilter())
    # Binarize the image
    image = image.point(lambda x: 0 if x < 140 else 255, '1')
    return image

def extract_score_from_text(text, question):
    if "積分" in question:
        team_name = question.split("請問")[1].split("的積分")[0].strip()
        lines = text.split('\n')
        for line in lines:
            if team_name in line:
                # Extract the score from the line
                try:
                    # 假設積分是行中的最後一個數字
                    parts = line.split()
                    for part in parts:
                        if part.isdigit():
                            score = int(part)
                            return score
                except ValueError:
                    continue
    return None

def generate_hw04(question):
    try:
        # Preprocess the image
        image = preprocess_image('baseball.png')
        
        # Use OCR to extract text from the image with Traditional Chinese language and table recognition
        text = pytesseract.image_to_string(image, lang='chi_tra', config='--psm 6')
        
        # Print the extracted text for debugging
        # print("Extracted text from image:")
        # print(text)
        
        # Process the extracted text to find the answer to the question
        score = extract_score_from_text(text, question)
        
        if score is not None:
            # Format the result as specified
            result = {
                "Result": {
                    "score": score
                }
            }
        else:
            # Use langchain to answer the question based on the extracted text
            llm = use_llm()
            message = HumanMessage(content=f"以下是從圖片中提取的文字資料：\n{text}\n請用這樣的方式回答問題：舉例為中華台北，若是問某個隊伍的積分，則是回答積分數字 5498，若是問所屬大洲聯盟，則是只回答 BFA , 若是問排名，則是回答 1 。若是詢問排名第幾的隊伍，則是回答 2：{question}。")
            response = llm.invoke([message])
            # Extract the numeric score from the response
            score = int(''.join(filter(str.isdigit, response.content)))
            result = {
                "Result": {
                    "score": score, # Default score
                    # "error": None,
                }
            }
        
        # Ensure the output format matches the expected format
        result_json = json.dumps(result, ensure_ascii=False, indent=4)
        result_json = result_json.replace('{\n    "Result": {', '{\n    "Result":\n    {')
        return result_json
    except Exception as e:
        result = {
            "Result": {
                "score": str(e)
            }
        }
        result_json = json.dumps(result, ensure_ascii=False, indent=4)
        result_json = result_json.replace('{\n    "Result": {', '{\n    "Result":\n    {')
        return result_json

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
#question = "2024年台灣10月紀念日有哪些?"
#print(f"作業1答案...")
#response = generate_hw01(question)

#print(f"作業2答案...")
#response = generate_hw02(question)

#question2 = "2024年台灣10月紀念日有哪些?"
#question3 = '{"date": "10-31", "name": "蔣公誕辰紀念日"}'
#question3 = '{"date": "10-31", "name": "萬聖節"}'
#result_hw02 = generate_hw02(question2)
#print(f"作業2結果: {result_hw02}")
#print(f"作業3答案...")
#response = generate_hw03(question2, question3)

print(f"作業4答案...")
question = "請問中華台北的積分是多少"
response = generate_hw04(question)

#print(f"作業4答案...")
#question = "請問中華台北的積分是多少"
#response = generate_hw04(question)

print(response)