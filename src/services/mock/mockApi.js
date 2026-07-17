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

function seedReviews() {
  const deleted = loadJson(STORAGE_KEYS.deletedPeerReviews, []);
  return seedPeople
    .map((person, index) => ({
      id: `review-${person.id}-seed`,
      personId: person.id,
      reviewer: ["王珂", "赵敏", "林知夏", "运营管理员"][index % 4],
      date: reviewDates[index % reviewDates.length],
      text: person.peerPortrait,
    }))
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
  return clone(loadJson(STORAGE_KEYS.peerReviews, []).concat(seedReviews()));
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
  saveJson(STORAGE_KEYS.peerReviews, reviews.filter((item) => !item.id.endsWith("-seed")));
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
