import { defineStore } from "pinia";
import {
  getActiveUserId,
  getTodayText,
} from "../state.js";
import {
  createReview as createServerReview,
  deleteReview as deleteServerReview,
  fetchSentReviews,
} from "../services/api/reviews.js";
import { getMockReviews, saveMockReviews } from "../services/mock/mockApi.js";
import { isServerMode } from "../services/mode.js";
import { useAuthStore } from "./auth.js";

export const useReviewsStore = defineStore("reviews", {
  state: () => ({
    reviews: getMockReviews(),
    loaded: false,
  }),
  getters: {
    sentReviews() {
      const auth = useAuthStore();
      return this.reviews.filter((item) => item.reviewer === auth.displayName && !item.id.endsWith("-seed"));
    },
    receivedReviews() {
      return this.reviewsForPerson(getActiveUserId());
    },
  },
  actions: {
    persist() {
      if (!isServerMode()) saveMockReviews(this.reviews);
    },
    async loadReviews() {
      if (this.loaded && !isServerMode()) return;
      this.reviews = isServerMode() ? await fetchSentReviews() : getMockReviews();
      this.loaded = true;
    },
    reviewsForPerson(personId) {
      return this.reviews
        .filter((item) => item.personId === personId)
        .sort((left, right) => String(right.date).localeCompare(String(left.date)));
    },
    tagFor(review) {
      return String(review.tag || review.text || "").trim();
    },
    tagsForPerson(personId) {
      const tags = new Map();
      this.reviewsForPerson(personId).forEach((review) => {
        const tag = this.tagFor(review);
        if (!tag) return;
        const entry = tags.get(tag) || { tag, reviewers: new Set(), latestDate: review.date };
        entry.reviewers.add(review.reviewer);
        if (String(review.date) > String(entry.latestDate)) entry.latestDate = review.date;
        tags.set(tag, entry);
      });
      return [...tags.values()]
        .map((entry) => ({ tag: entry.tag, count: entry.reviewers.size, latestDate: entry.latestDate }))
        .sort((left, right) => right.count - left.count || String(right.latestDate).localeCompare(String(left.latestDate)));
    },
    async saveReview(payload) {
      if (payload.personId === getActiveUserId()) return { ok: false, message: "不能为自己补充他画像" };
      const tag = String(payload.tag || payload.text || "").trim();
      if (!tag) return { ok: false, message: "请选择或填写事项" };
      const auth = useAuthStore();
      const existing = this.reviews.find((item) =>
        item.personId === payload.personId &&
        item.reviewer === auth.displayName &&
        this.tagFor(item) === tag
      );
      const record = {
        id: payload.id || existing?.id || `review-${Date.now()}`,
        personId: payload.personId,
        reviewer: auth.displayName,
        date: payload.date || getTodayText(),
        tag,
      };
      const saved = isServerMode() ? await createServerReview(record) : record;
      this.reviews = [saved || record, ...this.reviews.filter((item) => item.id !== record.id)];
      this.persist();
      return { ok: true, record };
    },
    async deleteReview(reviewId) {
      if (isServerMode()) await deleteServerReview(reviewId);
      this.reviews = this.reviews.filter((item) => item.id !== reviewId);
      if (reviewId.endsWith("-seed")) {
        const deleted = JSON.parse(localStorage.getItem("firstResponsibilityDemo.deletedPeerReviews") || "[]");
        localStorage.setItem("firstResponsibilityDemo.deletedPeerReviews", JSON.stringify(Array.from(new Set(deleted.concat(reviewId)))));
      } else {
        this.persist();
      }
    },
  },
});
