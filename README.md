# Sephiria Guide (sephiria-guide.com)

Fan guides for the Steam roguelite **Sephiria** (Team Horay).  
三层分离（航海关卡 7）：框架 / 配置 / 内容。加一篇内页 = 往 `content/` 丢一个 JSON 再 build。

## Layers

| Layer | Where | Change when |
|---|---|---|
| Framework | `build.py`, `assets/styles.css` | Almost never |
| Config | `config/site.json` → writes `assets/theme.css` | New game / rebrand |
| Content | `content/*.json` | Every page |

```bash
python3 build.py
python3 tools/check_seo_consistency.py   # 唯一 H1 / canonical / sitemap↔磁盘
python3 tools/swap_test.py          # 换游戏名只改配置的验证
python3 -m http.server 8765 --bind 127.0.0.1
# http://127.0.0.1:8765/
```

关卡 8 提示词在仓库外：`../关卡8_内页清单与提示词.md`。

## Pages

Generated from `content/`. Current set includes home, guides hub, beginner, builds, companion, weapons, Destiny, Hard Mode, wishing fountain, artifacts, bosses (Erma / final), multiplayer, secret rooms, costumes, scythe.

## Notes

- Content is sourced from Steam + cross-checked guides/videos (no fabricated game facts).
- Unofficial fan site; not affiliated with Team Horay.
- Live: https://sephiria-guide.com/
