import { defineStore } from "pinia";
import {
  currentUserId,
  getTodayText,
  normalize,
  normalizeContentRecord,
  splitTags,
} from "../state.js";
import {
  createContent as createServerContent,
  deleteContent as deleteServerContent,
  fetchContents,
  toggleContentPin as toggleServerContentPin,
  updateContent,
} from "../services/api/content.js";
import { getMockContent, saveMockContent } from "../services/mock/mockApi.js";
import { isServerMode } from "../services/mode.js";

function sortContent(left, right) {
  return Number(right.pinned) - Number(left.pinned) || String(right.publishedAt).localeCompare(String(left.publishedAt));
}

export const useContentStore = defineStore("content", {
  state: () => ({
    contents: getMockContent(),
    activeContentId: "",
    loaded: false,
  }),
  getters: {
    sortedContents: (state) => state.contents.slice().sort(sortContent),
    myContent() {
      return this.contents.filter((item) => item.ownerId === currentUserId).sort(sortContent);
    },
  },
  actions: {
    persist() {
      if (!isServerMode()) saveMockContent(this.contents);
    },
    async loadContents() {
      if (this.loaded && !isServerMode()) return;
      this.contents = isServerMode() ? await fetchContents() : getMockContent();
      this.loaded = true;
    },
    getContent(id) {
      return this.contents.find((item) => item.id === id);
    },
    contentByOwner(ownerId) {
      return this.contents.filter((item) => item.ownerId === ownerId).sort(sortContent);
    },
    filteredMyContent(keyword) {
      const key = normalize(keyword);
      if (!key) return this.myContent;
      return this.myContent.filter((item) =>
        normalize(`${item.title} ${item.tags.join(" ")} ${item.summary} ${item.body}`).includes(key)
      );
    },
    isOwnContent(item) {
      return item?.ownerId === currentUserId;
    },
    async saveContent(payload) {
      const editingId = payload.editingId || payload.id || "";
      const existing = this.getContent(editingId);
      const record = normalizeContentRecord({
        id: editingId || `c-${Date.now()}`,
        ownerId: currentUserId,
        title: payload.title,
        tags: splitTags(payload.tagsText ?? payload.tags),
        summary: payload.summary,
        body: payload.body,
        publishedAt: existing?.publishedAt || getTodayText(),
        pinned: existing?.pinned || false,
        weeklyQueryCount: existing?.weeklyQueryCount || payload.weeklyQueryCount || 12,
        weeklyRecommendCount: existing?.weeklyRecommendCount || payload.weeklyRecommendCount || 8,
      });
      if (isServerMode()) {
        const saved = editingId ? await updateContent(editingId, record) : await createServerContent(record);
        const normalized = normalizeContentRecord(saved || record);
        if (editingId) this.contents = this.contents.map((item) => (item.id === editingId ? normalized : item));
        else this.contents.unshift(normalized);
        this.activeContentId = normalized.id;
        return normalized;
      }
      if (editingId) this.contents = this.contents.map((item) => (item.id === editingId ? record : item));
      else this.contents.unshift(record);
      this.activeContentId = record.id;
      this.persist();
      return record;
    },
    async deleteContent(id) {
      const item = this.getContent(id);
      if (!this.isOwnContent(item)) return false;
      if (isServerMode()) await deleteServerContent(id);
      this.contents = this.contents.filter((record) => record.id !== id);
      if (this.activeContentId === id) this.activeContentId = "";
      this.persist();
      return true;
    },
    async toggleContentPin(id) {
      const item = this.getContent(id);
      if (!this.isOwnContent(item)) return false;
      if (isServerMode()) await toggleServerContentPin(id, { pinned: !item.pinned });
      item.pinned = !item.pinned;
      this.persist();
      return true;
    },
  },
});
