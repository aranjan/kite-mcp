# kite-mcp Promotion Plan

## Week 1 (March 25-31)

### Day 1 - Reddit
- [ ] Post to r/zerodha
- Title: "Built an open-source MCP server for Zerodha -- trade through AI conversation instead of code"
- Use the Reddit draft (saved below)

### Day 2 - X/Twitter + LinkedIn
- [ ] Post tweet with tags @zeaboradha #MCP #Zerodha #OpenSource
- [ ] Post LinkedIn professional version
- Use drafts saved below

### Day 3 - Reddit (second post)
- [ ] Post to r/IndianStreetBets (more casual tone)

### Day 4 - Reddit (third post)
- [ ] Post to r/developersIndia (focus on technical/MCP angle)

### Day 5 (Tuesday-Thursday) - Hacker News
- [ ] Post "Show HN" between 5:30-7:30pm IST (8-10am ET)
- Title: Show HN: kite-mcp -- Trade Indian stocks on Zerodha via AI conversation (MCP server)
- URL: https://github.com/aranjan/kite-mcp
- Add the first comment immediately after posting (see draft below)

### Ongoing
- [ ] Monitor and respond to comments on all posts
- [ ] Check PR status: awesome-mcp-servers #3891, official MCP servers #3704
- [ ] Check Glama review status

---

## Week 2 (April 1-7)

### Blog post
- [ ] Write "How I built an MCP server to trade stocks through AI" on Dev.to
- Structure: problem, why MCP, TOTP automation challenge, FastMCP migration, demo
- Include code snippets and conversation screenshots
- [ ] Cross-post to Hashnode

### Demo video
- [ ] Screen record 2-min demo in Claude Desktop
- Flow: check portfolio -> get quote -> place order -> check order status
- [ ] Upload to YouTube
- [ ] Add video link to README

### Zerodha community
- [ ] Post on tradingqna.com
- [ ] Share in Zerodha Telegram/Discord groups

---

## Week 3-4 (April 8-21)

### Feature updates
- [ ] Pick one roadmap item to build (option chain data or basket orders)
- [ ] Release new version
- [ ] Post update on X/LinkedIn/Reddit ("kite-mcp v0.2 -- now with option chain data")

### Track metrics
- [ ] Check PyPI downloads: pypistats.org/packages/kite-mcp
- [ ] Check GitHub stars and forks
- [ ] Check Smithery installs

---

## Month 2-3

### Improvements
- [ ] Upgrade to publisher Kite Connect app (unlocks live quotes)
- [ ] Add demo mode with mock data (helps Smithery score + onboarding)
- [ ] Build Slack bot wrapper for real-time trading

### Repeat promotion
- [ ] Post about new features on Reddit/X/LinkedIn
- [ ] Submit to any new MCP directories that emerge

---

## Draft Posts

### Reddit (r/zerodha, r/IndianStreetBets)

Title: Built an open-source MCP server for Zerodha -- trade through AI conversation instead of code

I got tired of writing scripts every time I wanted to automate something on Kite, so I built kite-mcp -- an MCP server that lets any MCP-compatible AI assistant trade on Zerodha on your behalf.

Instead of writing Python code, you just say things like:
- "Buy 50 Reliance at market price"
- "How's my portfolio doing?"
- "Set a stop-loss GTT on my BDL at 1100"

The AI checks the quote, verifies you have enough funds, asks for confirmation, and places the order.

Features:
- 14 tools: holdings, positions, orders, margins, live quotes, OHLC, historical data, place/modify/cancel orders, GTT triggers
- Fully automated daily login with TOTP -- no manual token refresh
- Auto-retries if a token expires mid-session
- Supports CNC (delivery), MIS (intraday), and NRML (F&O)

You need a Kite Connect API subscription from Zerodha.

Install: pip install kite-mcp
GitHub: github.com/aranjan/kite-mcp

MIT licensed. Feedback welcome. Happy to answer questions.

---

### X/Twitter

Just shipped kite-mcp -- an open-source MCP server that lets you trade Indian stocks on Zerodha through natural conversation with AI assistants.

"Buy 50 Reliance at market price" -- and it just does it.

14 tools: holdings, orders, quotes, GTT triggers, historical data, and more.

pip install kite-mcp

github.com/aranjan/kite-mcp

#MCP #Zerodha #OpenSource #Trading #AI

---

### LinkedIn

I built and open-sourced kite-mcp -- an MCP server that connects Zerodha Kite to any MCP-compatible AI assistant.

The problem: Trading on Zerodha programmatically requires writing Python scripts, managing authentication tokens that expire daily, and handling API quirks.

The solution: kite-mcp lets you trade through natural conversation:

- "Buy 50 Reliance at market price"
- "Show my portfolio with P&L"
- "Set a stop-loss on HAL at 3400"

No code. No scripts. The AI assistant handles symbol mapping, fund verification, and order execution.

What it includes:
- 14 trading tools (holdings, positions, orders, quotes, GTT triggers, historical data)
- Fully automated TOTP login -- zero manual intervention
- Auto-retry on expired tokens
- Supports delivery, intraday, and F&O orders

Built with Python, FastMCP, and the Kite Connect API. MIT licensed.

pip install kite-mcp
GitHub: github.com/aranjan/kite-mcp
PyPI: pypi.org/project/kite-mcp

If you trade on Zerodha and use AI assistants, give it a try. Feedback and contributions welcome.

#OpenSource #MCP #Zerodha #Trading #AI #Python #Fintech

---

### Hacker News (first comment after posting)

I built an open-source MCP server that connects Zerodha Kite (India's largest retail broker) to any MCP-compatible AI assistant.

Instead of writing Python scripts to trade, you say things like "Buy 50 Reliance at market price" and the assistant checks the quote, verifies your funds, asks for confirmation, and places the order.

14 tools: holdings, positions, orders, margins, quotes, historical data, place/modify/cancel orders, and GTT triggers.

The interesting technical bits:
- Fully automated TOTP login (generates 2FA codes on the fly using pyotp)
- Auto-retries when Kite invalidates tokens mid-session
- Built with FastMCP, so each tool is just a decorated Python function with type hints
- Falls back to portfolio data for quotes on personal API plans

pip install kite-mcp | MIT licensed

Happy to answer questions about MCP, the Kite Connect API, or the architecture.

---

### Dev.to blog post outline

Title: How I Built an MCP Server to Trade Stocks Through AI

1. The problem -- trading on Zerodha requires scripts
2. What is MCP and why it matters
3. The architecture: You -> AI -> kite-mcp -> Kite API
4. The TOTP automation challenge (daily token expiry)
5. Migrating from raw MCP SDK to FastMCP
6. The quote fallback for personal API plans
7. Making it public: PyPI, GitHub, Smithery
8. Demo: a real trading conversation
9. What's next: option chains, basket orders, mutual funds

---

### Zerodha TradingQ&A

Title: Open-source MCP server for Kite Connect -- trade via AI conversation

Hi everyone,

I've built an open-source MCP (Model Context Protocol) server for Kite Connect that lets you interact with your Zerodha account through natural language via any MCP-compatible AI assistant.

Instead of writing API code, you can say "Buy 50 Infosys" and the assistant handles symbol lookup, fund verification, confirmation, and order placement.

14 tools included: holdings, positions, orders, margins, quotes, OHLC, historical data, instruments search, place/modify/cancel orders, and GTT triggers.

It also handles automated TOTP login daily -- no manual token refresh needed.

Install: pip install kite-mcp
Source: github.com/aranjan/kite-mcp
License: MIT

Would love feedback from the community. Contributions welcome.
