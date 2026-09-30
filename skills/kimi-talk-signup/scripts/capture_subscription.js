// Wildcard · for KIMI Talk — 订阅页主控截取脚本（Kimi WebBridge evaluate 注入执行）
// 设计目标：一次注入拿全结果，把 agent 侧往返压到最少（稳态 3 次调用完成整条链）。
// 返回 status 三态：
//   ok           已在订阅页且已登录，fields 为实测字段
//   needs_login  检测到未登录/被踢到登录流程
//   wrong_page   地址或页面结构变了，agent 需退回 SKILL.md 探路兜底流程
// 实测校准（2026-09-28，真实页面两轮验证）。

(async () => {
  const SUB_PATH = "/settings/subscription";
  const TIERS = ["Allegro", "Moderato", "Andante", "Max", "Plus", "Pro", "Go"];
  const MAX_RAW = 2000;

  // 态 0：不在 kimi.com（例如被重定向到登录页/其他域）
  if (!/(^|\.)kimi\.com$/i.test(location.hostname)) {
    return { status: "wrong_page", url: location.href, note: "not_on_kimi_domain" };
  }

  // SPA 页面跳转后内容异步渲染：轮询等待订阅面板出现（最多 10 秒）。
  // 注意：左侧设置导航会先渲染，必须以面板特征词（有效期/总使用量/登录引导）为准，不能只看正文非空。
  const getText = () => ((document.querySelector("main") || document.body).innerText || "")
    .replace(/\n{2,}/g, "\n").trim();
  let text = getText();
  const deadline = Date.now() + 10000;
  while (!/有效期|总使用量|登录|注册/.test(text) && Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, 200));
    text = getText();
  }

  // 态 1：未登录信号——订阅页无「有效期」且出现登录/注册引导
  if (!text.includes("有效期") && /登录|注册|sign in/i.test(text.slice(0, 400))) {
    return { status: "needs_login", url: location.href };
  }

  // 态 2：地址变了但还在 kimi.com（结构漂移）
  if (!location.pathname.startsWith(SUB_PATH) && !text.includes("总使用量")) {
    return { status: "wrong_page", url: location.href, note: "path_changed" };
  }

  const fields = {};
  fields.plan = (() => {
    const before = text.slice(0, Math.max(text.indexOf("有效期"), 0) || text.length);
    for (const t of TIERS) {
      if (new RegExp(`\\b${t}\\b`).test(before)) return t;
    }
    return null; // 未匹配到付费梯级，可能为免费用户
  })();

  const vu = text.match(/有效期至[:：]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})/);
  fields.valid_until = vu ? vu[1] : null;

  const up = text.match(/总使用量\s*\n?\s*([0-9]+(?:\.[0-9]+)?%)/);
  fields.usage_percent = up ? parseFloat(up[1]) : null;

  // 订阅起始与历史条数不在本页，需「账单与发票」页，留 null（不编造）
  fields.member_since = null;
  fields.subscription_count = null;

  fields.code_usage = (() => {
    const out = {};
    const m5 = text.match(/5\s*小时用量[\s\S]{0,40}?([0-9]+(?:\.[0-9]+)?%)/);
    const m7 = text.match(/7\s*天用量[\s\S]{0,40}?([0-9]+(?:\.[0-9]+)?%)/);
    if (m5) out.hours5 = parseFloat(m5[1]);
    if (m7) out.days7 = parseFloat(m7[1]);
    return Object.keys(out).length ? out : null;
  })();

  return {
    status: "ok",
    url: location.href,
    captured_at: new Date().toISOString(),
    page_title: document.title,
    fields,
    raw_text: text.slice(0, MAX_RAW),
  };
})()
