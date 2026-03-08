# 📚 每周论文汇总速递

自动抓取 ArXiv/Europe PMC 最新 AI 论文，使用 DeepSeek/Kimi 进行深度分析，并推送到飞书。
参考https://github.com/NN0202/arxiv_daily_paper_push.git改进

## ✨ 功能特性

- 🔍 **自动抓取**：每周自动获取 ArXiv 最新 LLM / AI Agent / Deep Learning 相关论文
- 🤖 **AI 深度分析**：调用 DeepSeek/Kimi API 生成结构化中文解读：
  - 【摘要原文】翻译摘要
  - 【核心洞察】核心问题与方法
  - 【逻辑推导】起承转合还原作者思路
  - 【方法设计】方法流程总结
  - 【专业知识解释】术语科普
- 💻 **代码链接**：自动从 PapersWithCode 匹配开源代码
- 📱 **飞书推送**：生成精美富文本卡片推送至飞书群

## 🚀 快速开始

### 1. 环境准备

```bash
pip install arxiv requests
```

### 2.配置

- 编辑 daily_paper.py，填写以下配置项：

```python
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/你的Webhook地址"
DEEPSEEK_API_KEY = "你的DeepSeek API Key"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # 或你的API地址，例如：https://api.moonshot.cn/v1/chat/completions
```

- 飞书 Webhook：在飞书创建群组 → 进入群组 → 设置-群机器人 → 添加机器人 → 自定义机器人 → 获取 Webhook 地址
  - 参考：https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot
- API Key：在开放平台 获取 
  - DeepSeek:https://platform.deepseek.com
  - Kimi:https://platform.moonshot.cn/console

### 3.设置每日/每周自动运行（Windows 任务计划程序）

1. 搜索打开「任务计划程序」
2. 点击右侧「创建基本任务」
3. 名称：ArXiv每日论文推送
4. 触发器：选择「每天」，设置运行时间（如 09:00）
5. 操作：选择「启动程序」
6. 程序或脚本：C:\Users\你的用户名\Desktop\run_arxiv.bat（或实际路径）
7. 起始于：C:\Users\你的用户名\Desktop
8. 完成：勾选「当单击"完成"时，打开此任务属性的对话框」
9. 高级设置（可选）：
   「条件」→ 取消勾选「只有在计算机使用交流电源时才启动-笔记本电脑使用」
   「设置」→ 勾选「如果任务失败，按以下频率重新启动」

### 4.注意事项

- 确保网络可访问 ArXiv、DeepSeek/Kimi API 和飞书服务器
- 建议先手动运行测试，确认配置无误后再设置定时任务
- 如需修改论文查询关键词，编辑 daily_paper.py 中的 query 参数

## 🫡 私人定制
- 1. daily_paper_ai.py 专注于人工智能/计算机科学领域方向的论文检索，主要获取arxiv中的论文，可通过修改advanced_query调整关键词
- 2. daily_paper_bio.py 专注于生物科学领域方向的论文检索，主要获取arxiv/Europe PMC中的论文，可通过修改advanced_query调整关键词