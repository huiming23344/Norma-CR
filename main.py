import asyncio
import json
import os
import subprocess


from git import Repo
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel

# 加载 .env 文件中的环境变量
_ = load_dotenv()

# 从环境变量读取配置
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")  # 默认值

# 验证必需的配置
if not API_KEY:
    raise ValueError("缺少 API_KEY 配置，请在 .env 文件中设置")
if not BASE_URL:
    raise ValueError("缺少 BASE_URL 配置，请在 .env 文件中设置")


instructions = """
You are a specialised agent for maintaining and developing the XXXXXX codebase.

## Development Guidelines:

1. **Test Failures:**
   - When tests fail, fix the implementation first, not the tests
   - Tests represent expected behavior; implementation should conform to tests
   - Only modify tests if they clearly don't match specifications

2. **Code Changes:**
   - Make the smallest possible changes to fix issues
   - Focus on fixing the specific problem rather than rewriting large portions
   - Add unit tests for all new functionality before implementing it

3. **Best Practices:**
   - Keep functions small with a single responsibility
   - Implement proper error handling with appropriate exceptions
   - Be mindful of configuration dependencies in tests

Remember to examine test failure messages carefully to understand the root cause before making any changes.
"""

provider = OpenAIProvider(
    api_key=API_KEY,
    base_url=BASE_URL,
)

model = OpenAIChatModel(
    MODEL_NAME,
    provider=provider,
)

context7 = MCPServerStdio(
    command="npx", args=["-y", "@upstash/context7-mcp"], tool_prefix="context"
)



agent = Agent(
    instructions=instructions,
    model=model,
    mcp_servers=[context7],
)


@agent.tool_plain()
def get_latest_commit_author_info(repo_path: str = '.') -> str | None:
    """
    Get the latest commit author information for the specified repo path.
    """
    try:
        # 打开给定路径的 Git 仓库
        repo = Repo(repo_path)
        
        # 确保是一个有效的 Git 仓库
        if repo.bare:
            print("No Git repository found.")
            return None
        
        # 获取最新一次提交
        latest_commit = repo.head.commit
        
        return latest_commit.author.name
    
    except Exception as e:
        print("Error accessing the Git repository:", e)
        return None

@agent.tool_plain()
def get_latest_commit_diffs_as_json(repo_path: str = '.') -> str | None:
    try:
        # 打开给定路径的 Git 仓库
        repo = Repo(repo_path)
        # 确保是一个有效的 Git 仓库
        if repo.bare:
            print("No Git repository found.")
            return None
        # 获取最新一次提交
        latest_commit = repo.head.commit
        
        # 检查是否有父提交
        if not latest_commit.parents:
            # 初始提交：获取所有文件作为新增内容
            print("这是初始提交，展示所有新增文件")
            diffs = latest_commit.diff(None, create_patch=True)
        else:
            # 获取最新提交与其父提交之间的差异
            diffs = latest_commit.diff(latest_commit.parents[0], create_patch=True)
        
        # 构建 diff 信息的字典列表
        diff_list = []
        for diff in diffs:
            # 获取 diff 内容并转换为字符串
            diff_content = diff.diff
            if isinstance(diff_content, bytes):
                diff_content = diff_content.decode('utf-8', errors='replace')
            elif diff_content is None:
                diff_content = "New file added or removed"
            
            diff_info = {
                "file_path": diff.a_path or diff.b_path,
                "diff": diff_content
            }
            diff_list.append(diff_info)
        
        # 将 diff 信息转换为 JSON 字符串
        json_diff = json.dumps(diff_list, ensure_ascii=False, indent=4)
        
        print("Latest Commit Diff as JSON:")
        print(json_diff)
        
        return json_diff
    except Exception as e:
        print("Error accessing the Git repository:", e)
        return None

async def main():
    # async with agent:
    #     await agent.to_cli()
    json_diff: str | None = get_latest_commit_diffs_as_json("/Users/luo/baidu/personal-code/nova-cr-agent")

    print(json_diff)



if __name__ == "__main__":
    asyncio.run(main())