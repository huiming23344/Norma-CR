import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from git_tools import get_last_commit_author

# 加载 .env 文件中的环境变量
_ = load_dotenv()

# 从环境变量读取配置
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")  # 默认值


if not BASE_URL:
    raise ValueError("缺少 BASE_URL 配置，请在 .env 文件中设置")

def get_api_key() -> str:
    if API_KEY:
        return API_KEY
    else:
        raise ValueError("API_KEY 未找到，请在 .env 文件中设置")


llm = ChatOpenAI(
    base_url=BASE_URL,
    api_key=get_api_key,
    model=MODEL_NAME,
    temperature=0.5,
    timeout=10,
)

agent = create_agent(
    model=llm,
    tools=[get_last_commit_author],
)

response= agent.invoke(
    {"messages": [{"role": "user", "content": "请你找出 /Users/luo/baidu/personal-code/nova-cr-agent 这个项目最近的commit提交人信息"}]}
)

print(response)
