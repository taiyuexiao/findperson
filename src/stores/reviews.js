import { defineStore } from "pinia";
import {
  currentUserId,
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
      return this.reviewsForPerson(currentUserId);
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
    async saveReview(payload) {
      if (payload.personId === currentUserId) return { ok: false, message: "不能为自己补充他画像" };
      if (!payload.text?.trim()) return { ok: false, message: "请填写评价内容" };
      const auth = useAuthStore();
      const record = {
        id: payload.id || `review-${Date.now()}`,
        personId: payload.personId,
        reviewer: auth.displayName,
        date: payload.date || getTodayText(),
        text: payload.text.trim(),
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
