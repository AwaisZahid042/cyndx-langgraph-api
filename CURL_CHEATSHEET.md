# Curl Cheat Sheet — Cyndx LangGraph API

Replace `BASE_URL` with your deployment URL or `http://localhost:8080` for local.

```bash
BASE_URL=https://cyndx-langgraph-api-xxxxx-uc.a.run.app
```

## Health Check

```bash
curl $BASE_URL/health | jq
```

## Create Session (default config)

```bash
curl -X POST $BASE_URL/sessions -H "Content-Type: application/json" -d '{}' | jq
```

## Create Session (custom model)

```bash
curl -X POST $BASE_URL/sessions -H "Content-Type: application/json" -d '{"agent_config": {"model": "llama-3.1-8b-instant", "temperature": 0.5}}' | jq
```

## Create Session (bring your own API key)

```bash
# Use your own OpenAI key on the live deployment
curl -X POST $BASE_URL/sessions -H "Content-Type: application/json" -d '{"agent_config": {"model": "gpt-4o-mini", "llm_api_key": "sk-your-key-here"}}' | jq

# Use your own Anthropic key
curl -X POST $BASE_URL/sessions -H "Content-Type: application/json" -d '{"agent_config": {"model": "claude-3-5-haiku-20241022", "llm_api_key": "sk-ant-your-key"}}' | jq
```

## Send Message

```bash
SESSION_ID=sess_YOUR_ID_HERE

curl -X POST $BASE_URL/sessions/$SESSION_ID/messages -H "Content-Type: application/json" -d '{"content": "What companies were acquired in the fintech space in 2024?"}' | jq
```

## Test Calculator Tool

```bash
curl -X POST $BASE_URL/sessions/$SESSION_ID/messages -H "Content-Type: application/json" -d '{"content": "What is 1547 * 382?"}' | jq
```

## Test DateTime Tool

```bash
curl -X POST $BASE_URL/sessions/$SESSION_ID/messages -H "Content-Type: application/json" -d '{"content": "What day of the week is today?"}' | jq
```

## Test Multi-Turn Memory

```bash
curl -X POST $BASE_URL/sessions/$SESSION_ID/messages -H "Content-Type: application/json" -d '{"content": "My name is Muhammad and I build AI products"}' | jq

curl -X POST $BASE_URL/sessions/$SESSION_ID/messages -H "Content-Type: application/json" -d '{"content": "What is my name and what do I do?"}' | jq
```

## Get Conversation History

```bash
curl $BASE_URL/sessions/$SESSION_ID/history | jq
```

## Delete Session

```bash
curl -X DELETE $BASE_URL/sessions/$SESSION_ID | jq
```

## Test Error Handling

```bash
# 404 — invalid session
curl $BASE_URL/sessions/sess_nonexistent/history | jq

# 422 — empty message
curl -X POST $BASE_URL/sessions/$SESSION_ID/messages -H "Content-Type: application/json" -d '{"content": ""}' | jq

# 400 — message to terminated session
curl -X DELETE $BASE_URL/sessions/$SESSION_ID | jq
curl -X POST $BASE_URL/sessions/$SESSION_ID/messages -H "Content-Type: application/json" -d '{"content": "Hello"}' | jq
```

## Swagger UI

Open in browser: `$BASE_URL/docs`
