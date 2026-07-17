import { defineStore } from "pinia";
import { loadJson, saveJson, STORAGE_KEYS } from "../state.js";
import { reportInteractionEvent } from "../services/agui/reporter.js";

export const useFeedbackStore = defineStore("feedback", {
  state: () => ({
    feedbackMap: loadJson(STORAGE_KEYS.feedback, {}),
  }),
  actions: {
    persist() {
      saveJson(STORAGE_KEYS.feedback, this.feedbackMap);
    },
    toggle(targetKey, value, context = {}) {
      this.feedbackMap[targetKey] = this.feedbackMap[targetKey] === value ? "" : value;
      this.persist();
      reportInteractionEvent({
        eventType: "feedback_toggle",
        targetId: targetKey,
        value: this.feedbackMap[targetKey],
        context,
      });
    },
  },
});
