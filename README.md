# CFO Telegram Bot

A personal CFO in your pocket — a Telegram bot with 11 financial expert roles, 25+ commands, AI-powered analysis, and charts. Built with Python, python-telegram-bot, Groq LLM, and SQLite.

**Platform:** Telegram  
**Bot:** [@YourBotName](https://t.me/YourBotName) *(replace with your actual bot link)*

---

## What It Does

Send any financial question as plain text and the bot routes it to the right expert. Or use specific commands for structured tasks: log transactions, track budgets, research stocks, simulate loans, manage a debt ledger, and generate financial ideas on demand.

---

## Commands

### Financial Manager
| Command | Description | Example |
|---------|-------------|---------|
| `/snapshot` | Monthly financial health report + expense chart | `/snapshot` |
| `/log` | Log an income or expense transaction | `/log expense food 15000 lunch` |
| `/decide` | Get a CFO verdict on a financial decision | `/decide should I buy a new laptop?` |

### Accountant
| Command | Description | Example |
|---------|-------------|---------|
| `/audit` | P&L audit + anomaly detection + pie chart | `/audit` |
| `/importcsv` | Bulk import transactions (pipe-separated rows) | `/importcsv 2026-04-01,expense,food,15000,lunch` |

### Budget Analyst
| Command | Description | Example |
|---------|-------------|---------|
| `/setbudget` | Set a monthly spending limit for a category | `/setbudget food 200000` |
| `/budget` | Actuals vs budget report + grouped bar chart | `/budget` |

### Investment Analyst
| Command | Description | Example |
|---------|-------------|---------|
| `/invest` | Mini research report on a stock + price chart | `/invest AAPL` |
| `/compare` | Compare two stocks side by side | `/compare AAPL MSFT` |
| `/portfolioadd` | Add/update a position in your portfolio | `/portfolioadd AAPL 10 150.00` |

### Risk Specialist
| Command | Description | Example |
|---------|-------------|---------|
| `/risk` | Portfolio risk analysis + optional stress test | `/risk market crash 30%` |

### Credit & Loans
| Command | Description | Example |
|---------|-------------|---------|
| `/creditcheck` | Creditworthiness check with DTI ratio | `/creditcheck 3000000 500000 10000000 car` |
| `/loan` | Loan payment + amortization breakdown | `/loan 10000000 12 5` |
| `/compareloans` | Compare two loan options | `/compareloans 10M 12 5 10M 10 7` |

### Financial Advisor
| Command | Description | Example |
|---------|-------------|---------|
| `/advise` | Holistic financial advice | `/advise should I pay off debt or invest?` |
| `/ontrack` | Savings rate check vs retirement goal | `/ontrack 3000000 20 60` |

### Property Appraiser
| Command | Description | Example |
|---------|-------------|---------|
| `/appraise` | Asset valuation with low/mid/high range | `/appraise real_estate 2BR UB 80sqm 2015` |

### Debt Ledger
| Command | Description | Example |
|---------|-------------|---------|
| `/owe` | Record money you owe someone | `/owe Bilguun 50000 lunch 2026-04-20` |
| `/owed` | Record money someone owes you | `/owed Togi 20000 coffee` |
| `/settle` | Mark all entries with a person as settled | `/settle Bilguun` |
| `/ledger` | View full outstanding debt ledger | `/ledger` |

### 💡 Brainstorm
| Command | Description | Example |
|---------|-------------|---------|
| `/brainstorm` | Generate personalised financial ideas on any topic | `/brainstorm how to save more` |
| `/income_ideas` | New income stream and side hustle ideas | `/income_ideas` |
| `/costcuts` | Spending cuts without hurting lifestyle | `/costcuts` |
| `/goals` | 3/6/12-month financial goal roadmap | `/goals` |

### AI Chat
Send any plain text message and the bot responds as a personal CFO using your last 30 days of transaction data as context.

---

## Example Interactions

**Brainstorm income ideas:**
```
User: /brainstorm income
Bot: 💡 Brainstorm: Income

1. **Freelance Financial Modeling** — High impact
   Your accounting background maps directly to freelance Excel/financial model work on Upwork.

2. **Monetize Your Investing Knowledge** — Medium impact
   Given your AAPL/MSFT portfolio, consider writing a paid newsletter or Substack...
...
7. 🃏 Wildcard: Peer-to-peer lending via a local fintech platform — lend small amounts at 18-24% APR.
```

**Log and snapshot:**
```
User: /log expense food 45000 groceries
Bot: Logged: expense 45,000.00 — food (groceries)

User: /snapshot
Bot: 📊 Financial Snapshot
Income:   1,500,000.00
Expenses:   320,000.00
Net:      1,180,000.00
[+ bar chart + AI analysis]
```

**Stock research:**
```
User: /invest NVDA
Bot: 📈 NVIDIA Corporation (NVDA)
Price: 875.40 | P/E: 65.2
[30-day price chart]
Valuation: Premium but justified by AI tailwinds...
```

---

## Setup

### Prerequisites
- Python 3.11+
- Telegram bot token from [@BotFather](https://t.me/botfather)
- Groq API key from [console.groq.com](https://console.groq.com)

### Local
```bash
git clone https://github.com/yourusername/cfo-telegram-bot.git
cd cfo-telegram-bot

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your tokens

python bot.py
```

### Deploy to Railway (recommended)

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select this repo
4. Add environment variables in Railway dashboard:
   - `TELEGRAM_TOKEN` — your bot token
   - `GROQ_API_KEY` — your Groq key
5. Railway auto-detects the Dockerfile and deploys

The bot runs 24/7 on Railway's free tier.

---

## Project Structure

```
cfo-telegram-bot/
├── bot.py                  # Entry point, handler registration
├── modules/
│   ├── financial_manager.py  # /snapshot /log /decide
│   ├── accountant.py         # /audit /importcsv
│   ├── budget_analyst.py     # /setbudget /budget
│   ├── investment_analyst.py # /invest /compare /portfolioadd
│   ├── risk_specialist.py    # /risk
│   ├── credit_analyst.py     # /creditcheck
│   ├── financial_advisor.py  # /advise /ontrack
│   ├── loan_officer.py       # /loan /compareloans
│   ├── property_appraiser.py # /appraise
│   ├── credit_clerk.py       # /owe /owed /settle /ledger
│   ├── brainstormer.py       # /brainstorm /income_ideas /costcuts /goals
│   └── prompts.py            # LLM system prompts per role
├── utils/
│   ├── db.py                 # SQLite setup and connection
│   ├── groq_client.py        # Groq LLM wrapper
│   └── charts.py             # matplotlib chart generators
├── data/                     # SQLite database (gitignored)
├── Dockerfile
├── railway.toml
├── requirements.txt
└── .env.example
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_TOKEN` | Bot token from @BotFather |
| `GROQ_API_KEY` | API key from console.groq.com |

---

## Git Workflow

This project was developed using git worktrees for parallel feature development:

```bash
# Core setup on main
git worktree add ../cfo-bot-investment feature/investment-analyst
git worktree add ../cfo-bot-brainstorm feature/brainstorm

# Work on two features simultaneously without branch switching
```

Each feature was tracked as a GitHub issue → feature branch → PR → merge.
