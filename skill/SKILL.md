---
name: knowledge-base-api
description: |
  Manage a P.A.R.A.-structured personal knowledge base through a local RESTful API. 
  Use this skill when the user wants to create, read, update, delete, search, or organize 
  notes in their knowledge base. Supports full-text search, semantic search, and intelligent 
  P.A.R.A. classification. The API runs locally at http://127.0.0.1:8000.
metadata:
  short-description: Knowledge base CRUD & search via REST API
---

# Knowledge Base API Skill

Local REST API for P.A.R.A. knowledge base management.

## Quick Reference

**Base URL**: `http://127.0.0.1:8000`  
**Auth**: JWT Bearer token in `Authorization` header.

### 1. Authenticate

```
POST /auth/login
Body: {"username": "admin", "password": "..."}
→ {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
```

Use `access_token` as `Authorization: Bearer <token>` on all subsequent requests.

### 2. Notes CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notes?path=&recursive=false` | List directory |
| GET | `/notes/{path}` | Read file or list dir (auto) |
| POST | `/notes/{path}` | Create file/dir |
| PUT | `/notes/{path}` | Update file content |
| DELETE | `/notes/{path}?archive=true` | Delete (default: archive) |

**Create**: `POST /notes/00_Inbox/new-note.md` with `{"content": "# Title\n...", "is_directory": false}`  
**Update**: `PUT /notes/00_Inbox/new-note.md` with `{"content": "updated content"}`

### 3. Search

**Full-text**: `POST /search` with `{"q": "keyword", "path": "", "use_regex": false}`  
**Semantic**: `POST /search/semantic` with `{"query": "概念描述", "top_k": 10}`  
**Rebuild index**: `POST /search/index` (admin only, required before first semantic search)

### 4. Classification

**Suggest category**: `POST /classify/suggest` with `{"title": "note title", "content": "..."}`  
Returns ranked P.A.R.A. category suggestions with confidence scores.

**Move note**: `POST /classify/move` with `{"src": "00_Inbox/note.md", "dst": "20_Areas/22_Finance/note.md"}`

### 5. P.A.R.A. Structure

All paths are relative to the knowledge base root:

- `00_Inbox` — Temporary landing zone for unprocessed content
- `10_Projects` — Active projects with deadlines
- `20_Areas` — Long-term responsibilities (Health, Finance, Development, SocialNet, Other)
- `30_Resources` — Reference material by topic (Hard/Soft Skills, Philosophy, etc.)
- `40_Assets` — Personal output: templates, code snippets, content
- `90_Archives` — Completed or inactive content

### Workflow: Process Inbox

1. `GET /notes?path=00_Inbox` — list unprocessed items
2. For each item: `GET /notes/00_Inbox/{file}` — read content
3. `POST /classify/suggest` — get category suggestion
4. `POST /classify/move` — move to suggested path

### Error Handling

- `401`: Invalid/expired token → refresh or re-login
- `403`: Permission denied (path not in whitelist or missing permission)
- `404`: File/directory not found
- `409`: File already exists (on create)
