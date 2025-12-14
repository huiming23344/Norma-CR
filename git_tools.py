"""
Git工具函数模块
使用GitPython包操作Git仓库
"""

from git import Repo
from pathlib import Path


def get_last_commit_author(repo_path: str) -> dict[str, str]:
    """
    获取指定文件夹路径下git最后一个commit的提交人信息
    
    Args:
        repo_path: Git仓库的文件夹路径
        
    Returns:
        dict: 包含提交人信息的字典，格式为：
            {
                'name': 提交人姓名,
                'email': 提交人邮箱,
                'commit_hash': commit的SHA值,
                'commit_message': commit信息,
                'commit_date': commit日期
            }
            
    Raises:
        Exception: 如果路径不是有效的Git仓库或其他错误
    """
    try:
        # 将路径转换为Path对象并确保是绝对路径
        resolved_repo_path = Path(repo_path).resolve()
        
        # 打开Git仓库
        repo = Repo(resolved_repo_path)
        
        # 获取最后一个commit
        last_commit = repo.head.commit
        
        # 提取提交人信息
        author_info = {
            'name': str(last_commit.author.name),
            'email': str(last_commit.author.email),
            'commit_hash': str(last_commit.hexsha),
            'commit_message': str(last_commit.message.strip()),
            'commit_date': str(last_commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S'))
        }
        
        return author_info
        
    except Exception as e:
        raise Exception(f"获取Git提交信息失败: {str(e)}")


# 使用示例
if __name__ == "__main__":
    # 测试函数
    try:
        # 使用当前目录作为示例
        author_info = get_last_commit_author(".")
        print("最后一次提交信息：")
        print(f"提交人: {author_info['name']}")
        print(f"邮箱: {author_info['email']}")
        print(f"Commit Hash: {author_info['commit_hash']}")
        print(f"提交信息: {author_info['commit_message']}")
        print(f"提交时间: {author_info['commit_date']}")
    except Exception as e:
        print(f"错误: {e}")


