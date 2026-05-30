# 试卷切片工具 (XDFclier)

纯规则引擎的 DOCX 试卷智能切片工具，一键部署到 Vercel。

## 快速部署

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

1. 点击上方按钮，或 Fork 本仓库后在 Vercel 导入
2. 框架选 **Other**，无需配置任何环境变量
3. 部署完成，访问域名即可使用

## 功能

- 上传 DOCX 试卷文件，自动识别题型范围
- 纯规则引擎，无需 LLM API Key
- 按题型分类输出排版精美的切片 DOCX
- 支持论述类文本、文学类文本、文言文阅读、古诗词阅读

## 本地开发

```bash
pip install -r api/requirements.txt
uvicorn cli.main:app --reload --port 8000
```

浏览器打开 `http://localhost:8000`。

## 技术栈

- **前端**: 单页 HTML (Codex 暗色风格)
- **后端**: Python FastAPI
- **部署**: Vercel (Python Serverless + Static)
- **处理**: 纯规则切片 (python-docx)

## 项目结构

```
├── api/               # Vercel Python Serverless
│   ├── index.py       # FastAPI 入口
│   └── requirements.txt
├── cli/               # Python 后端核心
│   ├── main.py        # FastAPI 服务
│   ├── scanner.py     # 题型扫描引擎
│   ├── slice_all.py   # DOCX 切片生成引擎
│   └── formatters/    # 格式渲染模块
├── frontend/          # Web 前端
│   └── index.html
└── vercel.json        # Vercel 配置
```
