import {
  createSession,
  currentUserId,
  getTodayText,
  loadJson,
  manualSections,
  normalizeContentRecord,
  normalizePersonRecord,
  reviewDates,
  saveJson,
  seedContent,
  seedPeople,
  splitTags,
  STORAGE_KEYS,
} from "./seed.js";

const clone = (value) => JSON.parse(JSON.stringify(value));

const seedReviewers = ["王珂", "赵敏", "林知夏", "运营管理员", "周弦", "叶澜", "宋可为", "唐沐", "何予", "蔡宁"];

const assistanceTagsByPerson = {
  "p-chen": ["大模型 Key 申请", "大模型 Key 申请", "大模型 Key 申请", "大模型 Key 申请", "HiAgent 平台使用", "HiAgent 平台使用", "HiAgent 平台使用", "模型调用", "模型调用", "智能体搭建"],
  "p-luo": ["指标口径确认", "指标口径确认", "指标口径确认", "数据报表核对", "数据报表核对", "数据报表核对", "数据质量排查", "数据质量排查", "数据来源追溯", "数据治理规范"],
  "p-song": ["系统权限申请", "系统权限申请", "系统权限申请", "账号开通", "账号开通", "账号开通", "系统故障排查", "系统故障排查", "应用登录异常", "运行监控"],
  "p-tang": ["流程审批咨询", "流程审批咨询", "流程审批咨询", "事项流转确认", "事项流转确认", "事项流转确认", "责任边界确认", "责任边界确认", "制度规范解释", "跨部门流程协调"],
  "p-xu": ["知识内容发布", "知识内容发布", "知识内容发布", "标签整理", "标签整理", "标签整理", "常见问题归档", "常见问题归档", "内容结构梳理", "运营规则咨询"],
  "p-lin": ["平台使用咨询", "平台使用咨询", "平台使用咨询", "问题流转跟进", "问题流转跟进", "问题流转跟进", "首问责任确认", "首问责任确认", "跨部门协同", "使用反馈收集"],
  "p-zhou": ["安全评估准备", "安全评估准备", "安全评估准备", "数据脱敏咨询", "数据脱敏咨询", "数据脱敏咨询", "审计材料准备", "审计材料准备", "风险整改跟进", "日志留存要求"],
  "p-jiang": ["政策口径咨询", "政策口径咨询", "政策口径咨询", "材料报送准备", "材料报送准备", "材料报送准备", "政策条款解读", "政策条款解读", "对外材料审核", "业务咨询答复"],
  "p-he": ["采购流程咨询", "采购流程咨询", "采购流程咨询", "预算占用确认", "预算占用确认", "预算占用确认", "合同付款办理", "合同付款办理", "资产登记咨询", "费用报销规则"],
  "p-ye": ["培训报名", "培训报名", "培训报名", "人员信息维护", "人员信息维护", "人员信息维护", "账号联动", "账号联动", "入职流程咨询", "离职权限回收"],
  "p-han": ["问题督办跟进", "问题督办跟进", "问题督办跟进", "投诉处理咨询", "投诉处理咨询", "投诉处理咨询", "闭环记录", "闭环记录", "响应时限确认", "服务反馈处理"],
  "p-cai": ["平台培训报名", "平台培训报名", "平台培训报名", "使用手册咨询", "使用手册咨询", "使用手册咨询", "宣贯材料准备", "宣贯材料准备", "平台操作答疑", "培训安排协调"],
};

function seedReviews() {
  const deleted = loadJson(STORAGE_KEYS.deletedPeerReviews, []);
  return seedPeople
    .flatMap((person, personIndex) => (assistanceTagsByPerson[person.id] || person.domains).map((tag, tagIndex) => ({
      id: `review-${person.id}-${tagIndex}-seed`,
      personId: person.id,
      reviewer: seedReviewers[tagIndex],
      date: reviewDates[(personIndex + tagIndex) % reviewDates.length],
      tag,
    })))
    .filter((item) => !deleted.includes(item.id));
}

export function getMockPeople() {
  const profile = loadJson(STORAGE_KEYS.profile, null);
  return clone(seedPeople.map((person) =>
    normalizePersonRecord(person.id === currentUserId && profile ? { ...person, ...profile } : person)
  ));
}

export function getMockContent() {
  return clone(loadJson(STORAGE_KEYS.content, seedContent).map(normalizeContentRecord));
}

export function getMockManualSections() {
  return clone(manualSections);
}

export function getMockReviews() {
  // Discard the previous free-text portrait records in favor of tag records.
  return clone(loadJson(STORAGE_KEYS.peerReviews, []).filter((item) => item.tag).concat(seedReviews()));
}

export function getMockSessions() {
  const sessions = loadJson(STORAGE_KEYS.sessions, [createSession()]);
  return clone(sessions.length ? sessions : [createSession()]);
}

export function saveMockProfile(profile) {
  saveJson(STORAGE_KEYS.profile, profile);
  return clone(profile);
}

export function saveMockContent(contents) {
  saveJson(STORAGE_KEYS.content, contents);
  return clone(contents);
}

export function saveMockReviews(reviews) {
  saveJson(STORAGE_KEYS.peerReviews, reviews.filter((item) => !item.id.endsWith("-seed") && item.tag));
  return clone(reviews);
}

export function saveMockSessions(sessions) {
  saveJson(STORAGE_KEYS.sessions, sessions);
  return clone(sessions);
}

export function createMockContent(payload) {
  const contents = getMockContent();
  const record = normalizeContentRecord({
    id: payload.id || `c-${Date.now()}`,
    ownerId: currentUserId,
    title: payload.title,
    tags: splitTags(payload.tagsText ?? payload.tags),
    summary: payload.summary,
    body: payload.body,
    publishedAt: payload.publishedAt || getTodayText(),
    pinned: Boolean(payload.pinned),
    weeklyQueryCount: payload.weeklyQueryCount || 12,
    weeklyRecommendCount: payload.weeklyRecommendCount || 8,
  });
  contents.unshift(record);
  saveMockContent(contents);
  return record;
}
