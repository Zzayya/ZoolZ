# ZoolZ Core

This folder holds ZoolZmstr, the small control layer that makes ZoolZ environment-aware and manages shared processes.

## Modules

- `ZoolZmstr/detection.py` — detects server vs laptop by checking for `~/Desktop/SERVER`.
- `ZoolZmstr/folder_manager.py` — returns environment-aware paths and creates `~/Desktop/ZoolZData/` on the server (uploads, outputs, database, logs). Modeling saves stay in the repo so they can sync.
- `ZoolZmstr/process_manager.py` — starts/stops shared helpers (Redis + Celery for Modeling) when programs are accessed.
- `ZoolZmstr/health_monitor.py` — logs basic system stats on the server.
- `ZoolZmstr/launcher.py` — placeholder for future program isolation.

The package is re-exported from `zoolz/ZoolZmstr/__init__.py` for easy imports:

```python
from zoolz.ZoolZmstr import is_server, get_environment, get_data_paths, process_manager
```

## Server marker

Create `~/Desktop/SERVER` on the Mac server to enable server mode:

```bash
touch ~/Desktop/SERVER
```

Without the marker, ZoolZ runs in laptop/dev mode and stores data inside the repo.
