import json
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from nova_cr_agent.config import load_openai_config
from nova_cr_agent.models import AgentState, FileCRResult
from tools.git_tools import get_last_commit_diff

model_config = load_openai_config(timeout=600)
llm = ChatOpenAI(
    base_url=model_config.base_url,
    api_key=model_config.api_key,
    model=model_config.model_name,
    temperature=model_config.temperature,
    timeout=model_config.timeout,
)



PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是一名资深代码审查专家，请严格按照 FileCRResult 的结构化模式返回结果，并确保所有文字说明使用中文。"),
    ("human",
     "请审查以下文件 diff。\n"
     "规则：\n"
     "- 如果是二进制文件或补丁为空：needs_human_review=true，并说明原因。\n"
     "- 行号尽量使用新版本的编号；如果不确定可填 null。\n"
     "- overall_severity 应等于最严重问题的级别。\n\n"
     "输入(JSON)：\n{payload_json}")
])

MAX_PATCH_CHARS = 12000

def _payload(file_diff) -> dict:
    patch = file_diff.patch or ""
    if len(patch) > MAX_PATCH_CHARS:
        patch = patch[:MAX_PATCH_CHARS] + "\n\n...<PATCH TRUNCATED>..."

    return {
        "file_path": file_diff.b_path or file_diff.a_path or "<unknown>",
        "change_type": file_diff.change_type,
        "is_binary": file_diff.is_binary,
        "added_lines": file_diff.added_lines,
        "deleted_lines": file_diff.deleted_lines,
        "patch": patch,
        # 其余字段随你保留
    }


prepare = RunnableLambda(lambda fd: {"payload_json": json.dumps(_payload(fd), ensure_ascii=False)})

# 关键：结构化输出
llm_structured = llm.with_structured_output(FileCRResult)

# 关键：重试（结构化解析/校验失败时）
review_chain = (prepare | PROMPT | llm_structured).with_retry(
    stop_after_attempt=3,
    retry_if_exception_type=(ValidationError, ValueError),
)

def review_file_diff(file_diff) -> FileCRResult:
    return review_chain.invoke(file_diff)


def review_commit_diff(state: AgentState):
    commit_diff = state["commit_diff"]
    result = review_file_diff(commit_diff.files[-3])
    return {
        "file_cr_result": [result],
    }
    
    
def print_commit_diff(state: AgentState) -> None:
    print(state["commit_diff"].files[-3])

def print_resule(state: AgentState):
    print(state["file_cr_result"])

def build_review_agent():
    """Construct and compile the LangGraph review agent."""
    agent_builder = StateGraph(AgentState)
    agent_builder.add_node("get_last_commit_diff", get_last_commit_diff)
    agent_builder.add_node("print_commit_diff", print_commit_diff)
    agent_builder.add_node("review_commit_diff", review_commit_diff)
    agent_builder.add_node("print_resule", print_resule)

    agent_builder.add_edge(START, "get_last_commit_diff")
    agent_builder.add_edge("get_last_commit_diff", "print_commit_diff")
    agent_builder.add_edge("print_commit_diff", "review_commit_diff")
    agent_builder.add_edge("review_commit_diff", "print_resule")
    agent_builder.add_edge("print_resule", END)
    return agent_builder.compile()


review_agent = build_review_agent()


def run_default_repo():
    repo_root = "/Users/luo/baidu/bcc/nova-go"
    # repo_root = str(Path(__file__).resolve().parent)
    return review_agent.invoke({"repo_path": repo_root})


if __name__ == "__main__":
    run_default_repo()


#  todo 处理截断问题