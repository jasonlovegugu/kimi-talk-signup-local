---
name: wildcard-for-kimi
description: 浏览 Kimi Talk 及 Kimi 官方社区线下活动、在对话里完成报名。装完后首次使用自动弹出真实活动列表并引导完成报名：深度/付费用户可授权后读取本人 Kimi 订阅信息进行快速核验，走 Wildcard 免审直通通道；报名表单对话式代填（含 Luma 付费/邀请/审批变体）。也用于活动组织者查看报名与分层结果。触发词：Kimi Talk、活动报名、线下活动、报名、Wildcard、Y 卡、深度用户通道、开始使用、最近有什么活动、查看报名。
---

# Wildcard for Kimi

**Wildcard** 是通用的线下活动报名分层工具：真爱粉亮出订阅证明，免审直通；其余用户正常排队。本插件是 Wildcard 系列的 Kimi 版（后续可出 Wildcard for Grok / Wildcard for ChatGPT 等版本，骨架复用）。

两类用户两条路：

- **普通通道**：所有人可报，收集基本信息后进入正常审核队列。
- **Wildcard 直通通道**：用户授权后，通过 Kimi WebBridge 在**用户自己的浏览器**里读取其 Kimi「我的订阅」页的公开可见信息（当前套餐、用量、订阅起始时间、历史订阅数），截图 + 结构化字段上传后端，规则打分达标即标记为直通（免审），不达标回落普通通道。

## 前置配置（首次使用时一次性完成）

向活动组织者（Jason）索取并记录到工作区 `backend/config.json`（**不要写进任何会随插件分发的文件**）：

- `supabase_url` / `supabase_service_key`：后端项目地址与服务端密钥（applications 表与 proofs 存储桶）。
- `submit_endpoint`：`submit-application` Neon Function 的公开 URL。
- `signup_endpoint`：`submit-signup` Neon Function 的公开 URL（写 signups 临时报名表 + users 长期用户标记）。
- `luma_endpoint` + `luma_admin_key`：`luma-register` Neon Function 的 URL 与调用密钥。

数据库：Neon（PostgreSQL 18）。组织者查库用工作区 `backend/neon/query.py`（连接串读 `backend/config.json`），不要在对话里让用户提供数据库密码。后端建表与部署步骤见工作区 `backend/README.md`。配置缺失时明确告诉用户"后端还没配好"，不要假装报名成功。

## Onboarding：首次使用引导（装完后第一次对话自动进入）

触发：本会话首次加载本技能、用户还没看过活动列表时；或用户说「开始使用 / 最近有什么活动 / 怎么用」。

1. **活动呈现（人工维护清单制，同流程 A 第 2 条）**：`data/events.json` 是组织者**人工维护的唯一真实来源**，里面只应有真实存在、报名链接已发布的活动。展示前**逐条实际打开链接验证**（页面真实存在、时间地点一致），然后展示：活动名、时间、地点、名额、真实 Luma 链接。清单为空 → 直接如实告知「最近没有可报名的活动，之后随时可以问我最近有哪些活动」。**绝不展示清单之外的活动，绝不编造、绝不展示无链接或验证不通过的条目。**
2. **用户选场后进入 Y 卡报名流**：先一句话说明两条通道的区别，问走哪条：
   - **Wildcard 直通**：走流程 C——用 WebBridge 在用户自己的浏览器里打开 kimi.com「我的订阅」页抓画面，提取套餐/用量等信息，跑打分脚本判定用户水平（fast_pass 深度用户 / fast_review 进阶 / standard 普通）；
   - **普通通道**：走流程 B，只收基本信息。
3. **帮用户完成报名（流程 E）**：拿到活动真实链接后进入报名表单页，用对话式代填完成提交；遇到 Luma 的各类变体（付费、邀请制、审批制、第三方表单）按流程 E 的变体规则处理。

## 流程 A：浏览活动

1. 读取 `data/events.json`，按城市/时间分组展示：活动名、时间、地点、名额、是否 Kimi Talk 主活动、Luma 链接、状态。
2. **人工维护清单制（不可妥协）**：只展示 `data/events.json` 清单里、且带真实可验证链接的活动——清单由组织者人工维护，**没有链接的活动根本不应该出现在清单里**；万一发现无链接或验证不通过的条目，不向用户展示，直接提醒组织者更新清单。展示前对链接实际打开验证一次（页面真实存在、时间地点一致）。清单为空就如实说「最近没有活动」。**绝不展示清单之外的活动，绝不编造、绝不展示未验证的链接。**
3. 用户表现出报名意向时，主动说明两条通道的区别，询问走哪条（深度直通需授权读取订阅信息，普通通道只需基本信息）。

## 流程 B：普通报名

1. 依次收集：姓名、联系方式（邮箱或微信，至少一个）、想参加的活动、一句话动机（可选）。
2. 组装 JSON 调用打分脚本（无订阅证明时 proof 为空，脚本会返回 standard）：

   ```bash
   python3 scripts/score_application.py '<proof-json字符串或文件路径>'
   ```

3. 通过 Neon Function 提交（截图字段留空）：

   ```bash
   curl -sS -X POST "<submit_endpoint>" -H "Content-Type: application/json" -d '<报名JSON>'
   ```

   报名JSON 结构：`{event_id, name, contact, track, decision, proof, screenshot_base64: null}`。
4. 提交成功后，紧接着登记长期用户标记 + 临时报名表（见「用户标记登记」，所有通道共用）。
5. 告知用户：报名已进入审核队列，结果通过其留下的联系方式通知。**不得承诺必过。**

## 流程 C：深度用户直通（核心流程）

### C1 知情授权（必须，不可跳过）

向用户展示并征得同意，话术要点：
- 将打开用户自己的浏览器、进入 kimi.com 的「我的订阅」页面；
- 只读取四项信息：当前套餐、当前用量、最早订阅时间、历史订阅条数，并截一张该页面截图；
- 读取完成后会把将上传的内容逐条展示给用户确认，用户可以随时中止；
- 不上传任何密码、支付信息、cookie，截图仅用于本次活动核验。

用户不同意或中途反悔 → 直接转流程 B，不得反复劝说。

### C2 浏览器内截取（Kimi WebBridge）

1. `list_tabs` 找已打开的 kimi.com 标签页，没有则 `navigate` 打开 `https://www.kimi.com` 并让用户登录（轮询等登录完成）。
2. 进入订阅页（2026-09 实测路径，优先直跳）：`navigate` 到 `https://www.kimi.com/settings/subscription`。备选路径：点左下角头像 → 菜单「会员计划」→ 页面顶部「我的订阅」标签。确认页面出现「有效期至」「用量进度」即到位。
3. 读取 `scripts/capture_subscription.js` 调 `evaluate` 注入执行。返回 `{url, captured_at, fields, raw_text}`，`fields` 实测结构：`{plan, valid_until, usage_percent, code_usage, member_since: null, subscription_count: null}`——订阅起始时间与历史订阅条数不在本页，如需可再开同页「账单与发票」标签读取，读不到就留 null，**不要编造**。
4. 对订阅页区域 `screenshot` 存为本地临时图片（jpg quality 70 即可，控制在 2 MB 内），准备上传。

### C3 用户确认回显

把解析出的四项信息 + 截图路径完整展示给用户，明确问"确认上传这些信息用于本次活动报名吗？"。确认后才进入 C4。

### C4 打分与提交

1. 组装 proof JSON（实测字段结构）：`{plan, valid_until, usage_percent, code_usage, member_since, subscription_count, source_url, captured_at}`——订阅页能拿到前四项，后两项从「账单与发票」补或留 null。跑 `score_application.py` 得到 `decision`：
   - `fast_pass`：达标，标记免审直通；
   - `fast_review`：接近达标，进入快速人工复核（组织者 1 分钟内可批）；
   - `standard`：回落普通通道。
2. 截图转 base64 后连同报名JSON 提交 Edge Function。
3. 提交成功后，登记长期用户标记 + 临时报名表（见「用户标记登记」）。
4. 告知用户结果：
   - fast_pass → "已直通，活动开始前会收到 Luma 邀请"；
   - fast_review → "已进入快速复核，通常当天有结果"；
   - standard → 转普通通道话术。

### C5 兜底

- 订阅页结构变化导致脚本抽不到字段：用 `snapshot` 读页面，把相关可见文本整理进 proof，并在 `proof.note` 标注"手工解析"。
- WebBridge 不可用（用户未装插件）：提示用户改用普通通道，或手动截图会员页后通过对话上传，走 fast_review。

## 流程 E：报名页对话式代填（Luma 等外部表单）

用户选场并选定通道后，帮他把报名表单填完并提交：

1. 用 WebBridge 打开活动的真实 Luma 链接（或组织者提供的其他报名页），`snapshot` 读取表单结构：字段、必填项、选项、费用、注册方式（开放 / approval required / invite-only）。
2. **对话式提问代填**：把表单问题翻译成对话，反过来问用户（一次问 1~3 个，选择题给选项）；姓名、联系方式等已在流程 B/C 收过的信息直接复用，不重复问。答案必须是用户明确给出的，**不替用户编造**。
3. 逐字段填入后提交，回读页面确认结果（已提交 / 待审批 / 需付费等）并如实告知用户。
4. 变体处理：
   - **付费活动**：如实展示价格与权益，说明「是否付费由你决定」；用户确认后引导其自行完成支付——**不代付、不碰任何支付信息**；
   - **审批制 / 邀请制（approval required / invite-only）**：说明该场需要主办人审批或持邀请，提交后进入审批队列，结果通过 Luma/联系方式通知；
   - **需要 Luma 账号**：引导用户自己在浏览器里登录或注册，登录完成后继续代填；
   - **第三方表单**（非 Luma）：同样对话式代填，提交后截图或回读结果向用户确认。

## 流程 D：组织者查看报名（仅 Jason 触发）

1. 向 Jason 确认要查的活动。
2. 用工作区 `backend/neon/query.py` 查 applications 表（按 decision 分组：各通道人数、待复核名单 fast_review、proof 摘要）；截图是 bytea 存在行内，需要复核时导出为图片文件再看。
3. 复核通过/拒绝：`backend/neon/query.py --set-decision <application_id> <approved|declined>`。
4. 把通过名单推入 Luma：

   ```bash
   curl -sS -X POST "<luma_endpoint>" -H "Content-Type: application/json" -H "x-admin-key: <luma_admin_key>" -d '{"event_id":"<events表里的活动id>","application_ids":["..."]}'
   ```

   Neon Function 会调用 Luma 官方 API（public-api.lu.ma，POST /v1/events/guests/add）以 approved 状态添加 guest。这是**给用户发名额**的操作，执行前把名单和人数向 Jason 复述确认。

## 用户标记登记（所有报名通道共用，submit-application 成功后执行）

向 `<signup_endpoint>` POST：

```bash
curl -sS -X POST "<signup_endpoint>" -H "Content-Type: application/json" -d '<登记JSON>'
```

登记JSON 结构：`{user_id, form_data, is_paid, is_pro_user}`，字段取值规则：

- `user_id`：报名者邮箱（contact 是邮箱时）；邮箱缺失则用微信账号——这是跨活动识别同一人的键；
- `form_data`：`{event_id, name, contact, track, decision, score}`（结构化摘要即可，**不含截图、不含 proof 原文**）；
- `is_paid`：proof 的 plan 命中付费套餐（score 脚本的付费正则：Go/Plus/Pro/Max/会员等）或 valid_until 在未来 → `true`；普通通道无 proof → `false`；
- `is_pro_user`：`decision == "fast_pass"`（规则判定为深度/熟练用户）→ `true`，否则 `false`；
- `expires_in_days`：不传，用默认 30 天；到期由后端定时任务自动删除，users 表标记永久保留。

提交失败不影响报名主流程，但要如实告知用户"报名已收到，用户标记登记未成功"。

## 红线

- **活动清单人工维护、链接必须真实**：只展示 `events.json` 清单里且带真实链接的活动，展示前实际验证；清单外活动一律不出现；绝不编造链接。（详见流程 A 第 2 条）
- **不代付、不碰支付信息**：遇到付费报名，只如实呈现价格与权益，付费动作由用户自己完成。
- **表单答案来自用户**：对话式代填只填用户明确给出的答案，不替用户编造、不默认勾选。
- **不导出、不存储任何凭证**：cookie / token / 密码 / 支付信息一律不碰；浏览器读取仅依赖"用户自己已登录"这一前提。
- **授权先于读取，回显先于上传**；用户任何一步喊停就停。
- **数据最小化**：只传四项订阅信息 + 一张截图，不整页抓取其他内容。
- 订阅信息是"快速核验的侧面证明"，不是不可伪造的强证明——话术里不承诺"100% 验证"，只称"基于订阅信息的快速核验"。
- 截图 base64 单张上限 2 MB，超过先压缩再传。
- 所有写操作（提交报名、更新状态、推入 Luma）完成后如实回报结果，失败就明说失败原因。
