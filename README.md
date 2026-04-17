# MemPalace HTTP API

HTTP REST API wrapper for MemPalace memory system.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## API Endpoints

### Search
- `POST /api/mempalace/search` - Semantic search
- `GET /api/mempalace/wake-up` - Get startup context
- `GET /api/mempalace/status` - Get palace status

### Store
- `POST /api/mempalace/store` - Store single memory
- `POST /api/mempalace/store/conversation` - Store conversation
- `DELETE /api/mempalace/store/{drawer_id}` - Delete memory

### Knowledge Graph
- `POST /api/mempalace/kg/add` - Add triple
- `POST /api/mempalace/kg/query` - Query entity
- `POST /api/mempalace/kg/invalidate` - Invalidate fact
- `GET /api/mempalace/kg/timeline` - Get timeline
- `GET /api/mempalace/kg/stats` - Get KG stats

## Docker

```bash
docker compose up -d
```
