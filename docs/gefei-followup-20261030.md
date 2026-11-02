# 哥飞会话建议执行记录

*最后更新：2026-10-30*

## 目标与边界

以线上提交 29160b1 为基线落实尚未完成的 FM27 页面建议。沿用现有扁平 URL、JSON 内容层和 Python builder。不重写已上线的球员、mods、skins 内容；Sephiria 五份观察内容保留到 11 月 4 日复核窗口。本分支不发布生产。

## 已完成

- [x] 对照 PR #11–#13：跳过已发布的重复页合并、wiki 收敛、球员资料和 PBZ 展示版本说明。
- [x] 官方复核：免费 Preview 10 月 29 日 18:00 GMT 至 11 月 3 日 18:00 GMT；之后符合条件的预购与 Game Pass 用户可继续；存档可继承。
- [x] content/fm27-free-play.json：官方入口、访问步骤、免费/付费阶段、存档继承与平台边界。
- [x] content/fm27-logo-pack.json：下载来源、兼容性边界、安装核对与缺图排错；不复制作者下载包，不编造统一安装路径。
- [x] content/fm27-tactics.json：移除等待 Preview 开放的过期措辞，明确没有本机赛季测试。
- [x] content/fm27.json、fm27-mods.json、fm27-release-date.json：加入两个新页的内链。
- [x] 构建与现有 SEO 一致性门、换肤门通过；构建为 36 页。

## 发布前检查

- 代码审查通过后提交分支与 draft PR；不合并 main（main push 会自动发布 Cloudflare）。
- logo-pack 的兼容性来自当日已发布 mods 页的来源记录。此次对 sortitoutsi 的重新读取遇到 Cloudflare 校验，未冒充重新实测。
- 免费期结束时仅在确认窗口已结束后更新正文。此处没有新建定时器；更新清单保留在本文件。

## 后续按事实触发

- 11 月 4 日 02:00 Asia/Hong_Kong 后：免费页明确免费期结束；保留付费 Preview、官方入口与存档继承说明。不能直接写成所有 Preview 都结束。
- 11 月 4 日：按已有复核窗口检查 Sephiria 词族与页面，不因最佳单次排名改页。
- 11 月 10 日：依据正式版公告更新 Preview 和正式发售表述，复核 mod/skin 作者兼容声明。
- 没有可靠战术实测时，不新增 best tactic 或阵型参数页；球员资料沿用已上线来源，不生成虚构属性。

## 新方向核验状态

- Delta Reign：公开官方页确认产品与 11 月 6 日零售时间；卡牌张数不能证明或证伪 card list 搜索量。待核关键词需求、竞争与数据维护方式，不凭原会话数值立即开站。
- image fader：竞品有整体透明度、渐变、羽化、局部与批量功能；其排名和可复制流量未复核。与 image2base64 可能相接的需求是 PNG alpha 与背景变白排错，尚未改该仓库。
- Cantina、Meta Vibes：产品事实有公开来源；教程长尾需求和 SERP 空缺仍未测。官方文档存在不等于第三方不能做。
- 哥飞 MCP load_guide 本轮返回 ECONNRESET，已记健康台账，未继续收费调用。以上三方向需求核验未完成，不标记立项或淘汰。

## 验证命令

```sh
python3 build.py
python3 tools/check_seo_consistency.py
python3 tools/swap_test.py
```

官方依据：https://www.footballmanager.com/news/play-football-manager-27-launch-preview-free
