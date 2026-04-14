import io
import json
import time
import pdfplumber
import urllib3
import  os
import arxiv
from langchain_core.tools import tool
from .models import SearchPapersInput
from .core_wrapper import CoreAPIWrapper

@tool("search-papers", args_schema=SearchPapersInput)
def search_papers(query: str, max_papers: int = 1) -> str:
    """Search for scientific papers using the CORE API.

    Example:
    {"query": "Attention is all you need", "max_papers": 1}

    Returns:
        A list of the relevant papers found with the corresponding relevant information.
    """
    try:
        return CoreAPIWrapper(top_k_results=max_papers).search(query)
    except Exception as e:
        return f"Error performing paper search: {e}"

@tool("download-paper")
def download_paper(url: str) -> str:
    """Download a specific scientific paper from a given URL and save it locally.

    Example:
    {"url": "https://sample.pdf"}

    Returns:
        The paper content.
    """
    try:
        if "/abs/" in url:
            url = url.replace("/abs/", "/pdf/") + ".pdf"
        save_dir = "./downloaded_papers"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        http = urllib3.PoolManager(
            cert_reqs='CERT_NONE',
        )
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        max_retries = 5
        for attempt in range(max_retries):
            response = http.request('GET', url, headers=headers)
            if 200 <= response.status < 300:
                file_name = url.split('/')[-1]
                if not file_name.endswith('.pdf'):
                    file_name += ".pdf"

                file_path = os.path.join(save_dir, file_name)

                # 将原始二进制数据写入本地文件
                with open(file_path, "wb") as f:
                    f.write(response.data)
                print(f"✅ 文件已保存至: {file_path}")
                pdf_file = io.BytesIO(response.data)
                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                return text
            elif attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 2))
            else:
                raise Exception(f"Got non 2xx when downloading paper: {response.status} {response.text}")
    except Exception as e:
        return f"Error downloading paper: {e}"

@tool("ask-human-feedback")
def ask_human_feedback(question: str) -> str:
    """Ask for human feedback. You should call this tool when encountering unexpected errors."""
    return input(question)

@tool("latest-paper-search")
def latest_paper_search(query:str,max_results:int=5):
    """Search for the most recent scientific papers using the arXiv API.

Use this tool to retrieve the absolute latest pre-prints, especially for
publications from 2025 to 2026 that may not yet be indexed in other databases.

Example:
{"query": "Large Language Model Agents", "max_results": 5}

Returns:
    A formatted string containing paper titles, publication dates, authors,
    abstracts, and PDF links for the most recent results.
"""
    try:
        client = arxiv.Client()
        # 构造搜索对象，按发布日期降序排列
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )

        results = []
        for result in client.results(search):
            date_str = result.published.strftime("%Y-%m-%d")
            results.append(
                f"Title: {result.title}\n"
                f"Published: {date_str}\n"
                f"Authors: {', '.join(author.name for author in result.authors)}\n"
                f"Summary: {result.summary[:300]}...\n"
                f"URL: {result.pdf_url}\n"
                f"---"
            )

        if not results:
            return "No recent papers found on arXiv for this query."

        return "\n".join(results)
    except Exception as e:
        return f"Error searching arXiv: {str(e)}"
tools = [search_papers, download_paper, ask_human_feedback,latest_paper_search]
tools_dict = {tool.name: tool for tool in tools}
