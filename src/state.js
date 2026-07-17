// ═══════════════════════════════════════════════════════════════════════════
// state.js — 首问责任平台 数据层
// ═══════════════════════════════════════════════════════════════════════════
//
// 包含：localStorage 键名、种子人员、部门层级、推荐次数、种子内容、
//       操作手册章节、领域词典、当前用户、评价日期、导航项、工具函数
// ═══════════════════════════════════════════════════════════════════════════

// ── localStorage 键名 ──────────────────────────────────────────────────────
export const STORAGE_KEYS = {
  profile: "firstResponsibilityDemo.profile",
  content: "firstResponsibilityDemo.content",
  peerReviews: "firstResponsibilityDemo.peerReviews",
  deletedPeerReviews: "firstResponsibilityDemo.deletedPeerReviews",
  sessions: "firstResponsibilityDemo.sessions",
  agui: "firstResponsibilityDemo.agui",
  interactions: "firstResponsibilityDemo.interactions",
  auth: "firstResponsibilityDemo.auth",
  feedback: "firstResponsibilityDemo.feedback",
};

// ── 种子人员 ───────────────────────────────────────────────────────────────
// id / name / department / role / contact / domains / selfPortrait / peerPortrait / completeness
export const seedPeople = [
  {
    id: "p-chen", name: "陈亦舟", department: "数字能力中心", role: "大模型平台主管",
    contact: "13800001201",
    domains: ["大模型", "Key 申请", "模型调用", "智能体"],
    selfPortrait: "我负责大模型能力接入、Key 申请流程支持，以及智能体应用建设中的模型侧问题答疑。",
    peerPortrait: "熟悉大模型平台接入流程，能快速判断 Key、权限、额度和调用报错问题。",
    completeness: 98,
  },
  {
    id: "p-luo", name: "罗澄", department: "数据治理科", role: "数据治理专员",
    contact: "13800001202",
    domains: ["数据治理", "指标口径", "数据报表", "数据质量"],
    selfPortrait: "我主要负责指标口径管理、数据质量核查、报表字段解释和数据治理规范维护。",
    peerPortrait: "对跨部门报表口径很敏感，适合处理数据不一致、指标解释、数据来源追溯等问题。",
    completeness: 92,
  },
  {
    id: "p-song", name: "宋可为", department: "应用运维科", role: "系统运维主管",
    contact: "13800001203",
    domains: ["系统运维", "权限申请", "账号问题", "故障排查"],
    selfPortrait: "我负责内部系统账号开通、权限问题排查、应用故障定位和运行监控。",
    peerPortrait: "处理系统登录、权限、网络和应用异常经验丰富，能给出明确排查路径。",
    completeness: 88,
  },
  {
    id: "p-tang", name: "唐沐", department: "流程管理室", role: "流程审批负责人",
    contact: "13800001204",
    domains: ["流程审批", "制度规范", "事项流转", "责任边界"],
    selfPortrait: "我维护跨部门流程审批规则、事项流转路径和首问责任边界说明。",
    peerPortrait: "适合咨询流程卡点、责任归属、审批路径和制度解释类问题。",
    completeness: 90,
  },
  {
    id: "p-xu", name: "徐念", department: "内容运营组", role: "内容运营专员",
    contact: "13800001205",
    domains: ["内容运营", "知识发布", "标签体系", "常见问题"],
    selfPortrait: "我负责平台内容运营、标签体系维护、常见问题归档和个人发布内容整理。",
    peerPortrait: "能帮助同事把零散经验整理成可复用内容，适合知识发布和标签治理问题。",
    completeness: 86,
  },
  {
    id: "p-lin", name: "林知夏", department: "综合协同办公室", role: "平台用户",
    contact: "13800001206",
    domains: ["首问责任", "协同流转", "问题分派"],
    selfPortrait: "我负责首问责任制平台日常使用反馈、问题流转记录和跨部门协同跟进。",
    peerPortrait: "熟悉业务咨询入口和首问流转过程，适合反馈平台体验和协同效率问题。",
    completeness: 82,
  },
  {
    id: "p-zhou", name: "周弦", department: "安全合规科", role: "安全合规负责人",
    contact: "13800001207",
    domains: ["安全合规", "数据脱敏", "审计检查", "风险评估"],
    selfPortrait: "我负责系统上线安全评估、数据脱敏规则、审计检查材料准备和安全风险整改跟踪。",
    peerPortrait: "对合规材料和审计口径熟悉，适合咨询上线前安全检查、数据出境、日志留存和脱敏问题。",
    completeness: 91,
  },
  {
    id: "p-jiang", name: "蒋宁", department: "政策研究室", role: "政策解读专员",
    contact: "13800001208",
    domains: ["政策解读", "政策口径", "材料报送", "业务咨询"],
    selfPortrait: "我负责政策文件解读、对外材料口径确认、业务报送要求梳理和政策问答沉淀。",
    peerPortrait: "适合处理政策条款怎么理解、材料怎么写、对外口径怎么统一等问题。",
    completeness: 87,
  },
  {
    id: "p-he", name: "何予", department: "财务资产科", role: "采购与预算主管",
    contact: "13800001209",
    domains: ["采购流程", "预算管理", "合同付款", "资产登记"],
    selfPortrait: "我负责采购申请、预算占用、合同付款节点、固定资产入库和费用报销规则解释。",
    peerPortrait: "能快速判断采购事项该走哪个流程、需要哪些附件，以及付款和预算是否满足条件。",
    completeness: 89,
  },
  {
    id: "p-ye", name: "叶澜", department: "人事培训组", role: "培训与账号协同专员",
    contact: "13800001210",
    domains: ["培训报名", "人员信息", "入职离职", "账号联动"],
    selfPortrait: "我负责培训报名、人员信息变更、入职离职协同和账号权限联动通知。",
    peerPortrait: "适合咨询人员信息维护、培训安排、新员工账号开通和离职权限回收问题。",
    completeness: 84,
  },
  {
    id: "p-han", name: "韩书", department: "质量监督办", role: "督办评价专员",
    contact: "13800001211",
    domains: ["督办跟踪", "服务评价", "投诉处理", "闭环管理"],
    selfPortrait: "我负责问题督办、服务评价回收、投诉处理记录和跨部门闭环跟踪。",
    peerPortrait: "适合咨询问题迟迟未响应、责任流转不清、服务评价和投诉反馈类事项。",
    completeness: 86,
  },
  {
    id: "p-cai", name: "蔡宁", department: "培训推广组", role: "平台推广专员",
    contact: "13800001212",
    domains: ["平台培训", "使用手册", "宣贯材料", "用户答疑"],
    selfPortrait: "我负责平台培训安排、使用手册编写、宣贯材料维护和一线用户答疑。",
    peerPortrait: "适合咨询平台怎么用、培训怎么报名、操作手册在哪里和宣贯材料如何更新。",
    completeness: 86,
  },
];

// ── 部门层级映射 ───────────────────────────────────────────────────────────
// 三级部门 → [一级部门, 二级部门, 三级部门]
export const departmentHierarchyMap = {
  数字能力中心: ["数字化建设部", "智能能力处", "数字能力中心"],
  数据治理科: ["数字化建设部", "数据治理处", "数据治理科"],
  应用运维科: ["数字化建设部", "平台运维处", "应用运维科"],
  流程管理室: ["综合管理部", "流程运营处", "流程管理室"],
  内容运营组: ["综合管理部", "知识运营处", "内容运营组"],
  综合协同办公室: ["综合管理部", "协同服务处", "综合协同办公室"],
  安全合规科: ["风险管理部", "安全治理处", "安全合规科"],
  政策研究室: ["业务管理部", "政策研究处", "政策研究室"],
  财务资产科: ["综合管理部", "财务保障处", "财务资产科"],
  人事培训组: ["综合管理部", "组织人事处", "人事培训组"],
  质量监督办: ["服务管理部", "服务督导处", "质量监督办"],
  培训推广组: ["服务管理部", "宣贯推广处", "培训推广组"],
};

// ── 本周推荐次数 ───────────────────────────────────────────────────────────
export const recommendedCountMap = {
  "p-chen": 126,
  "p-luo": 103,
  "p-song": 91,
  "p-tang": 88,
  "p-xu": 72,
  "p-lin": 64,
  "p-zhou": 79,
  "p-jiang": 68,
  "p-he": 74,
  "p-ye": 61,
  "p-han": 57,
  "p-cai": 52,
};

// ── 种子内容 ───────────────────────────────────────────────────────────────
// id / ownerId / title / tags / summary / body / publishedAt / pinned / weeklyQueryCount / weeklyRecommendCount
export const seedContent = [
  {
    id: "c-key", ownerId: "p-chen",
    title: "大模型 Key 申请流程",
    tags: ["大模型", "Key 申请", "权限流程"],
    summary: "说明大模型 Key 的申请条件、审批节点、调用额度和常见驳回原因。",
    body: "申请前需明确用途、调用模型、预计额度和责任部门。提交后按部门负责人、平台管理员两级审批。",
    publishedAt: "2026-07-05", pinned: true, weeklyQueryCount: 82, weeklyRecommendCount: 64,
  },
  {
    id: "c-agent", ownerId: "p-chen",
    title: "智能体应用常见问题处理说明",
    tags: ["智能体", "模型调用", "故障排查"],
    summary: "整理智能体运行报错、模型无响应、工具调用失败等常见问题的排查方法。",
    body: "重点排查模型配置、网络连通性、工具权限与输入参数完整性。",
    publishedAt: "2026-07-04", pinned: true, weeklyQueryCount: 77, weeklyRecommendCount: 59,
  },
  {
    id: "c-report", ownerId: "p-luo",
    title: "数据报表口径核对清单",
    tags: ["数据报表", "指标口径", "数据质量"],
    summary: "给出跨部门报表口径核对步骤，帮助定位字段来源、统计周期和计算规则差异。",
    body: "先确认指标定义，再核对统计周期、数据来源表和口径变更记录。",
    publishedAt: "2026-07-03", pinned: false, weeklyQueryCount: 71, weeklyRecommendCount: 44,
  },
  {
    id: "c-auth", ownerId: "p-song",
    title: "内部系统权限申请注意事项",
    tags: ["权限申请", "账号问题", "系统运维"],
    summary: "说明系统权限申请材料、审批人选择、账号异常处理和权限回收规则。",
    body: "所有权限申请需关联岗位职责，离岗后 24 小时内完成权限回收。",
    publishedAt: "2026-07-02", pinned: false, weeklyQueryCount: 69, weeklyRecommendCount: 51,
  },
  {
    id: "c-flow", ownerId: "p-tang",
    title: "跨部门事项流转路径说明",
    tags: ["流程审批", "事项流转", "责任边界"],
    summary: "解释跨部门事项如何判断首问责任人、协助人和最终处理部门。",
    body: "首问人先受理，再判断责任归属，如需协同须同步记录协助链路。",
    publishedAt: "2026-07-01", pinned: true, weeklyQueryCount: 74, weeklyRecommendCount: 56,
  },
  {
    id: "c-security", ownerId: "p-zhou",
    title: "系统上线安全评估材料清单",
    tags: ["安全合规", "审计检查", "风险评估"],
    summary: "列出系统上线前需要提交的安全评估材料、日志留存要求、脱敏证明和整改闭环记录。",
    body: "材料需至少包含安全评估表、日志策略、整改清单和责任人确认记录。",
    publishedAt: "2026-06-30", pinned: false, weeklyQueryCount: 58, weeklyRecommendCount: 36,
  },
  {
    id: "c-policy", ownerId: "p-jiang",
    title: "政策口径确认与材料报送说明",
    tags: ["政策解读", "政策口径", "材料报送"],
    summary: "说明政策条款不明确时的确认路径、材料报送格式和对外答复口径留痕要求。",
    body: "建议先内部形成统一口径，再进行对外答复，并保留确认记录。",
    publishedAt: "2026-06-29", pinned: false, weeklyQueryCount: 46, weeklyRecommendCount: 29,
  },
  {
    id: "c-purchase", ownerId: "p-he",
    title: "采购申请到合同付款流程",
    tags: ["采购流程", "预算管理", "合同付款"],
    summary: "串联采购申请、预算占用、合同审批、验收确认和付款申请的关键节点。",
    body: "流程关键在预算校验、验收凭证和付款资料完整性。",
    publishedAt: "2026-06-28", pinned: false, weeklyQueryCount: 43, weeklyRecommendCount: 31,
  },
  {
    id: "c-training", ownerId: "p-ye",
    title: "培训报名与人员信息维护流程",
    tags: ["培训报名", "人员信息", "入职离职"],
    summary: "说明培训报名入口、人员信息变更、入职离职联动和账号开通通知路径。",
    body: "涉及人员信息变更时需同步组织、人事和系统账号三方。",
    publishedAt: "2026-06-27", pinned: false, weeklyQueryCount: 38, weeklyRecommendCount: 24,
  },
  {
    id: "c-supervise", ownerId: "p-han",
    title: "首问事项督办和闭环管理办法",
    tags: ["督办跟踪", "闭环管理", "服务评价"],
    summary: "说明首问事项超过响应时限后的督办机制、协同记录要求和闭环评价方式。",
    body: "超时事项需触发督办，闭环前必须补齐协同说明和结果反馈。",
    publishedAt: "2026-06-26", pinned: false, weeklyQueryCount: 35, weeklyRecommendCount: 22,
  },
  {
    id: "c-training-manual", ownerId: "p-cai",
    title: "平台培训报名和使用手册获取",
    tags: ["平台培训", "使用手册", "用户答疑"],
    summary: "说明平台培训报名方式、手册下载路径、常见操作问题和宣贯材料更新流程。",
    body: "新用户可先阅读手册，再报名体验场培训。手册版本按月更新。",
    publishedAt: "2026-06-25", pinned: true, weeklyQueryCount: 62, weeklyRecommendCount: 48,
  },
];

// ── 操作手册章节 ───────────────────────────────────────────────────────────
export const manualSections = [
  { title: "1. 登录与首页", body: "支持用户名/手机号 + 密码登录。进入后默认看到首问助手首页，可直接发起提问或进入历史对话。" },
  { title: "2. 智能问答与历史对话", body: "每次提问都会生成会话记录，支持搜索、标题修改和直接删除。" },
  { title: "3. 名片库与人员主页", body: "名片库支持一级、二级、三级部门联动筛选；点击名片可进入人员主页查看职责、画像和公开发布内容。" },
  { title: "4. 个人中心与后台", body: "个人中心可维护资料、发布内容、查看操作手册；后台支持查看人员规模、发布内容、本周推荐热度和周活趋势。" },
];

// ── 领域词典 ───────────────────────────────────────────────────────────────
// 领域名 → 匹配关键词列表（用于问题意图识别和人员匹配）
export const domainDictionary = {
  大模型: ["大模型", "模型", "llm", "key", "调用", "额度", "api"],
  智能体: ["智能体", "agent", "工具调用", "应用建设", "报错"],
  数据治理: ["数据", "治理", "质量", "字段", "来源"],
  指标口径: ["指标", "口径", "统计", "报表", "不一致"],
  系统运维: ["系统", "运维", "故障", "登录", "账号", "异常"],
  权限申请: ["权限", "申请", "开通", "审批", "账号"],
  流程审批: ["流程", "审批", "事项", "流转", "制度", "责任边界"],
  内容运营: ["内容", "发布", "知识", "标签", "常见问题"],
  安全合规: ["安全", "合规", "上线", "风险", "审计", "日志"],
  政策解读: ["政策", "条款", "口径", "解读", "材料", "报送"],
  采购流程: ["采购", "合同", "付款", "预算", "报销", "资产"],
  培训报名: ["培训", "报名", "课程", "人员信息", "入职", "离职"],
  督办跟踪: ["督办", "超时", "响应", "投诉", "评价", "闭环"],
  平台培训: ["培训", "手册", "宣贯", "怎么用", "操作", "答疑"],
};

// ── 当前登录用户 ───────────────────────────────────────────────────────────
export const currentUserId = "p-lin";

// ── 种子评价日期 ───────────────────────────────────────────────────────────
export const reviewDates = ["2026-07-05", "2026-07-03", "2026-06-29", "2026-06-26", "2026-06-21", "2026-06-16"];

// ── 导航项（图标在 App.vue 中绑定）──────────────────────────────────────────
export const navItems = [
  { view: "ask", label: "智能问答" },
  { view: "directory", label: "名片库" },
  { view: "mine", label: "个人中心" },
  { view: "admin", label: "后台管理" },
];

// ═══════════════════════════════════════════════════════════════════════════
// 工具函数
// ═══════════════════════════════════════════════════════════════════════════

/** 从 localStorage 读取 JSON，解析失败时返回 fallback */
export function loadJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

/** 将 value 序列化为 JSON 写入 localStorage */
export function saveJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

/** 返回今天日期的 ISO 文本，如 "2026-07-08" */
export function getTodayText() {
  return new Date().toISOString().slice(0, 10);
}

/** 将标签字符串拆分为数组，支持顿号、逗号、空格分隔 */
export function splitTags(value) {
  if (Array.isArray(value)) return value.map((item) => String(item).trim()).filter(Boolean);
  return String(value || "").split(/[、,，\s]+/).map((item) => item.trim()).filter(Boolean);
}

/** 统一小写去空格，用于模糊匹配 */
export function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

/** 规范化人员记录：补齐 departmentPath 和 recommendedCount */
export function normalizePersonRecord(person) {
  const department = person.department || person.departmentPath?.[2] || "未分组";
  return {
    ...person,
    department,
    departmentPath:
      Array.isArray(person.departmentPath) && person.departmentPath.length >= 3
        ? person.departmentPath.slice(0, 3)
        : (departmentHierarchyMap[department] || ["未分组", "未分组", department]),
    recommendedCount:
      typeof person.recommendedCount === "number"
        ? person.recommendedCount
        : (recommendedCountMap[person.id] || 0),
  };
}

/** 规范化内容记录：补齐所有字段默认值 */
export function normalizeContentRecord(item) {
  return {
    ...item,
    ownerId: item.ownerId || "p-lin",

    title: item.title || "未命名内容",
    tags: splitTags(item.tags),
    summary: item.summary || "",
    body: item.body || item.summary || "",
    status: item.status || "已发布",
    publishedAt: item.publishedAt || getTodayText(),
    pinned: Boolean(item.pinned),
    weeklyQueryCount: Number.isFinite(item.weeklyQueryCount) ? item.weeklyQueryCount : 0,
    weeklyRecommendCount: Number.isFinite(item.weeklyRecommendCount) ? item.weeklyRecommendCount : 0,
  };
}

/** 创建一条空白会话 */
export function createSession() {
  return {
    id: `session-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    title: "新对话",
    conversation: [],
    pendingAction: null,
    lastResult: null,
  };
}
