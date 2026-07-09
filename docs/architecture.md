# StockAI Architecture

StockAI is an agentic AI investment research platform.

## Core idea

Market data is converted into structured evidence by specialist agents. A CIO agent synthesizes agent outputs into an explainable investment decision.

## Agents

- Technical Agent: Heikin Ashi, RSI, moving averages, momentum, volatility
- ML Agent: model probability and prediction confidence
- Risk Agent: ATR, trend breakdown, drawdown, volatility
- Portfolio Agent: cash, holdings, exposure, position sizing
- CIO Agent: final investment memo and decision synthesis

## Modes

### Fast Mode
Deterministic specialist agents + Gemini CIO.

### Deep AI Mode
Specialist agents may call Gemini for richer reasoning, but this is optional because of API cost and quota limits.

## Future modules

- News Agent
- Fundamentals Agent
- Macro Agent
- Paper Trading Simulator
- Supabase persistence