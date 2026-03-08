import arxiv
import requests
import json
from datetime import datetime, timedelta, timezone
import urllib.parse
import time

# --- 配置区 ---
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/"    # 这里替换成你的webhook网址
DEEPSEEK_API_KEY = "sk-"  # 替换为你的api-key
DEEPSEEK_API_URL = "https://api.moonshot.cn/v1/chat/completions"

PWC_BASE_URL = "https://arxiv.paperswithcode.com/api/v0/papers/"

EUROPE_PMC_QUERY = """
("network control theory" OR "brain controllability" OR "brain observability") OR 
(("optimal control" OR "state transition") AND ("brain" OR "neural" OR "neuroscience" OR "fMRI" OR "EEG"))
"""

ARXIV_QUERY = """
("network control theory" OR "brain controllability" OR "brain observability") OR 
(abs:"optimal control" AND abs:"brain") OR (abs:"state transition" AND abs:"neural")
"""


def fetch_from_europe_pmc(days=7, max_results=10):
    """从 Europe PMC 获取文献 (覆盖 PubMed, bioRxiv, medRxiv)"""
    print("📡 正在检索 Europe PMC (含 PubMed & bioRxiv)...")
    
    # 计算日期范围
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # 构造查询语句：关键词 AND 日期限制
    query = f'({EUROPE_PMC_QUERY}) AND FIRST_PDATE:[{start_date} TO {end_date}]'
    encoded_query = urllib.parse.quote(query)
    
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={encoded_query}&format=json&resultType=core&pageSize={max_results}"
    
    papers = []
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            results = data.get('resultList', {}).get('result', [])
            
            for res in results:
                # 只保留有摘要的论文
                if 'abstractText' in res:
                    source = res.get('bookOrReportDetails', {}).get('publisher', res.get('journalTitle', 'bioRxiv/PubMed'))
                    url_link = f"https://europepmc.org/article/MED/{res.get('pmid')}" if 'pmid' in res else f"https://doi.org/{res.get('doi')}"
                    
                    papers.append({
                        "title": res.get('title'),
                        "summary": res.get('abstractText').replace('<p>', '').replace('</p>', ''),
                        "url": url_link,
                        "source": source,
                        "date": res.get('firstPublicationDate')
                    })
    except Exception as e:
        print(f"Europe PMC 检索出错: {e}")
        
    return papers


def fetch_from_arxiv(days=7, max_results=10):
    """从 ArXiv 获取物理/定量生物学交叉学科文献"""
    print("📡 正在检索 ArXiv (q-bio & physics)...")
    client = arxiv.Client()
    
    # 限制在定量生物学(q-bio)或物理学(physics)分类下
    full_query = f"((cat:q-bio.* OR cat:physics.soc-ph OR cat:cs.SI) AND ({ARXIV_QUERY}))"
    
    search = arxiv.Search(
        query=full_query, 
        max_results=30, # 先多取点，本地再按时间过滤
        sort_by=arxiv.SortCriterion.SubmittedDate 
    )
    
    time_limit = datetime.now(timezone.utc) - timedelta(days=days)
    papers = []
    
    try:
        results = list(client.results(search))
        for res in results:
            if res.published >= time_limit:
                papers.append({
                    "title": res.title,
                    "summary": res.summary.replace('\n', ' '),
                    "url": res.entry_id,
                    "source": "ArXiv",
                    "date": res.published.strftime("%Y-%m-%d")
                })
                if len(papers) >= max_results:
                    break
    except Exception as e:
        print(f"ArXiv 检索出错: {e}")
        
    return papers

def summarize_with_deepseek(paper):
    """使用 DeepSeek 进行论文摘要深度总结"""
    prompt_text = f"""你是一个生物医学工程、脑与认知科学、网络神经科学领域的研究生，目标是深入理解论文的方法部分，包括方法动机、设计逻辑、流程细节、优势与不足，以便学习和在研究中借鉴。你的角色是高效、深入的论文分析师。请根据以下论文的标题和摘要提供中文深度分析。
    论文标题: {paper['title']}
    论文摘要: {paper['summary']}

    【重要指令】请严格按照以下 Markdown 格式输出，必须包含 Emoji 和引用符号(>)，不要输出多余的寒暄废话：

    🥇 **【摘要原文】**
    * 翻译摘要原文
 
    🎯 **【核心洞察】**
    > (简练说明：a) 作者为什么提出这个方法？阐述其背后的驱动力。b) 现有方法的痛点/不足是什么？具体指出局限性。c) 论文的研究假设或直觉是什么？用简洁语言概括。)

    🧠 **【逻辑推导】**
    * **背景 (Context)**：作者为什么提出这个方法？阐述其背后的驱动力。
    * **破局 (Insight)**：作者是怎么灵光一现的？核心直觉是什么？

    ⚙️ **【方法设计】**
    * a) 给出清晰的方法流程总结（pipeline），逐步解释输入→处理→输出。必须讲清楚每一步的具体操作和技术细节。这一步必须非常细致，这是用户的主要阅读目标。
    * b) 如果涉及模型结构，请描述每个模块的功能与作用，以及它们如何协同工作。
    * c) 如果有公式/算法，请用通俗语言解释它们的意义和在方法中的角色。

    """

    payload = {
        "model": "kimi-k2-turbo-preview", 
        "messages": [
            {"role": "system", "content": "你是一个学术分析专家，擅长将复杂的生物医学工程、脑与认知科学、网络神经科学领域的论文总结得清晰易懂。"},
            {"role": "user", "content": prompt_text}
        ],
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        
        # 先检查 HTTP 状态码
        if response.status_code != 200:
            return f"HTTP 错误 {response.status_code}: {response.text[:200]}"
        
        # 安全解析 JSON
        try:
            res_json = response.json()
        except json.JSONDecodeError as e:
            return f"JSON 解析错误: {str(e)}\n原始响应: {response.text[:200]}"
        
        # 打印完整响应用于调试（可以注释掉）
        print(f"API 响应: {json.dumps(res_json, ensure_ascii=False, indent=2)}")
        
        # 检查各种可能的错误格式
        if not isinstance(res_json, dict):
            return f"API 返回非字典类型: {type(res_json)} - {str(res_json)[:200]}"
        
        if 'error' in res_json:
            error_msg = res_json['error']
            if isinstance(error_msg, dict):
                return f"DeepSeek API 报错: {error_msg.get('message', str(error_msg))}"
            else:
                return f"DeepSeek API 报错: {str(error_msg)}"
        
        # 检查 choices 是否存在且为列表
        if 'choices' not in res_json:
            return f"API 响应缺少 'choices' 字段。可用字段: {list(res_json.keys())}"
        
        choices = res_json['choices']
        if not isinstance(choices, list) or len(choices) == 0:
            return f"'choices' 字段格式错误: {choices}"
        
        # 安全获取第一条结果
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return f"choice[0] 不是字典: {type(first_choice)}"
        
        if 'message' not in first_choice:
            return f"choice 缺少 'message' 字段。可用字段: {list(first_choice.keys())}"
        
        message = first_choice['message']
        if not isinstance(message, dict):
            return f"message 不是字典: {type(message)}"
        
        if 'content' not in message:
            return f"message 缺少 'content' 字段。可用字段: {list(message.keys())}"
        
        return message['content']
        
    except Exception as e:
        return f"未预期的错误: {type(e).__name__}: {str(e)}"


def push_to_feishu(report_content):
    """发送飞书富文本卡片"""
    header = { "Content-Type": "application/json" }
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True,  # 【关键美化】开启宽屏模式，文字不挤
                "enable_forward": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"🚀 ArXiv 每日精选 · {datetime.now().strftime('%m-%d')}"
                },
                "template": "blue"  # 换成稳重的蓝色，比橙色更护眼
            },
            "elements": [
                # 顶部引言块
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "💡 **今日 AI 前沿论文已由 Agent 深度分析完毕，请阅览：**"
                    }
                },
                {"tag": "hr"}, # 分割线
                
                # 核心分析内容（原封不动保留 Markdown 的丰富排版！）
                {
                    "tag": "markdown",
                    "content": report_content
                },
                
                {"tag": "hr"},
                
                # 精美页脚
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"🤖 本摘要由 DeepSeek-V3 自动生成 | 抓取时间: {datetime.now().strftime('%H:%M')}"
                        }
                    ]
                }
            ]
        }
    }
    requests.post(FEISHU_WEBHOOK, headers=header, json=payload)

if __name__ == "__main__":
    print("🚀 启动生物医学/神经科学多源文献监控引擎...")
    
    # 1. 分别从两大库获取过去 7 天的文献
    pmc_papers = fetch_from_europe_pmc(days=7, max_results=7)
    arxiv_papers = fetch_from_arxiv(days=7, max_results=3)
    
    # 2. 合并结果
    all_papers = pmc_papers + arxiv_papers
    
    if not all_papers:
        print("💡 过去一周内没有找到符合该交叉领域的新论文。")
    else:
        # 最多只取前 10 篇进行分析，防止超出 token 和运行时间
        target_papers = all_papers[:10]
        print(f"🎯 数据源合并完毕，准备分析 {len(target_papers)} 篇核心文献...")
        
        full_report = ""
        
        for i, paper in enumerate(target_papers):
            print(f"🤖 正在分析第 {i+1}/{len(target_papers)} 篇 ({paper['source']}): {paper['title']}")
            
            # 调用大模型生成深度总结
            summary = summarize_with_deepseek(paper)
            
            # 拼装 Markdown 内容，加入数据库来源标签
            source_tag = f"`{paper['source']}`" 
            full_report += f"**📄 {i+1}. {paper['title']}**\n[🔗 来源: {source_tag} | 点击阅读原文]({paper['url']})\n\n{summary}\n\n---\n"
        
        print("🚀 分析完毕，正在推送到飞书...")
        push_to_feishu(full_report, len(target_papers))
        print("✅ 推送成功！")