# Sephiria Guide (sephiria-guide.com)

Fan guides for the Steam roguelite **Sephiria** (Team Horay).  
Built for the 生财航海「AI 产品（国外-热词游戏站）」关卡 4 — locally browsable English P0 site.

## Local preview

```bash
python3 -m http.server 8765 --bind 127.0.0.1
# open http://127.0.0.1:8765/
```

Regenerate HTML from research notes:

```bash
python3 build.py
```

## Pages (P0)

| Path | Intent |
|---|---|
| `/` | Home / sephiria |
| `/guides/` | Wiki hub |
| `/beginner-guide/` | Beginner |
| `/builds/` | Builds |
| `/weapons/` | Weapons |
| `/destiny-inscription/` | Destiny tree |
| `/artifacts/` | Artifacts & tablets |
| `/bosses/` `/bosses/erma/` `/bosses/final/` | Bosses |
| `/multiplayer/` | Co-op |
| `/secret-rooms/` | Secrets |
| `/costumes/` | Costumes |
| `/items/scythe/` | Blizzard Scythe / Drifa |

## Notes

- Content is sourced from Steam + cross-checked guides/videos (no fabricated game facts).
- Unofficial fan site; not affiliated with Team Horay.
- Target domain: `sephiria-guide.com` (deploy in later stage).
