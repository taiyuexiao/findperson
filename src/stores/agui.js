import { defineStore } from "pinia";
import { ElMessage } from "element-plus";
import { loadJson, normalizeContentRecord, saveJson, STORAGE_KEYS } from "../state.js";
import { connectAguiStream } from "../services/agui/transport.js";
import { createMockAguiStream } from "../services/agui/mockStream.js";
import { reportInteractionEvent } from "../services/agui/reporter.js";
import { useAuthStore } from "./auth.js";
import { useContentStore } from "./content.js";
import { useDirectoryStore } from "./directory.js";
import { useReviewsStore } from "./reviews.js";
import { useSessionsStore } from "./sessions.js";

export const useAguiStore = defineStore("agui", {
  state: () => ({
    activeRunId: "",
    streamStatus: "idle",
    messagesBySession: loadJson(STORAGE_KEYS.agui, {}).messagesBySession || {},
    cardsByMessage: loadJson(STORAGE_KEYS.agui, {}).cardsByMessage || {},
    pendingConfirmations: loadJson(STORAGE_KEYS.agui, {}).pendingConfirmations || {},
    activeDetail: { type: "empty" },
    isDetailSidebarVisible: false,
    lastError: "",
    abortController: null,
    timeoutHandle: null,
  }),
  getters: {
    activeMessages() {
      const session = useSessionsStore().activeSession;
      return session ? (this.messagesBySession[session.id] || []) : [];
    },
    isStreaming: (state) => state.streamStatus === "streaming",
  },
  actions: {
    persist() {
      saveJson(STORAGE_KEYS.agui, {
        messagesBySession: this.messagesBySession,
        cardsByMessage: this.cardsByMessage,
        pendingConfirmations: this.pendingConfirmations,
      });
    },
    ensureSession(sessionId) {
      if (!this.messagesBySession[sessionId]) this.messagesBySession[sessionId] = [];
    },
    async sendMessage(sessionId, text) {
      if (!text?.trim() || this.isStreaming) return;
      const sessions = useSessionsStore();
      const directory = useDirectoryStore();
      const content = useContentStore();
      const reviews = useReviewsStore();
      const auth = useAuthStore();
      const runId = `run-${Date.now()}`;
      const userMessageId = `msg-u-${Date.now()}`;
      const assistantMessageId = `msg-a-${Date.now()}`;
      this.activeRunId = runId;
      this.abortController = new AbortController();
      this.timeoutHandle = window.setTimeout(() => this.abortController?.abort(), 30000);
      this.streamStatus = "streaming";
      this.lastError = "";
      this.ensureSession(sessionId);
      this.messagesBySession[sessionId].push({
        id: userMessageId,
        role: "user",
        text: text.trim(),
        createdAt: new Date().toISOString(),
      });
      this.messagesBySession[sessionId].push({
        id: assistantMessageId,
        role: "assistant",
        text: "",
        streaming: true,
        analysis: null,
        createdAt: new Date().toISOString(),
      });
      sessions.patchSession(sessionId, {
        title: sessions.activeSession.title === "新对话" ? text.trim().slice(0, 28) : sessions.activeSession.title,
      });
      this.persist();

      const payload = {
        message: { id: userMessageId, role: "user", text: text.trim() },
        // assistantMessageId:服务端事件必须以此 ID 归属,否则前端无法匹配到助手气泡(server 模式契约)
        context: { userId: auth.userId, page: "ask", clientTraceId: runId, assistantMessageId },
      };
      const source = import.meta.env.VITE_AGUI_MODE === "server"
        ? connectAguiStream({ sessionId, payload, signal: this.abortController.signal, timeoutMs: 30000, retry: 1 })
        : createMockAguiStream({
            sessionId,
            runId,
            messageId: assistantMessageId,
            question: text.trim(),
            people: directory.activePeople,
            content: content.contents,
            reviewsForPerson: (personId) => reviews.reviewsForPerson(personId),
            currentUserId: auth.userId,
            authName: auth.displayName,
          });
      try {
        for await (const event of source) this.applyEvent(event);
      } catch (error) {
        this.applyEvent({ type: "run_error", sessionId, runId, messageId: assistantMessageId, message: error.message });
      }
    },
    applyEvent(event) {
      this.ensureSession(event.sessionId);
      if (event.type === "run_started") {
        const message = this.messagesBySession[event.sessionId].find((item) => item.id === event.messageId);
        if (message && event.result?.analysis) {
          message.analysis = event.result.analysis;
          message.result = event.result;
        }
      }
      if (event.type === "text_delta") {
        const message = this.messagesBySession[event.sessionId].find((item) => item.id === event.messageId);
        if (message) message.text += event.delta || "";
      }
      if (event.type === "text_finished") {
        const message = this.messagesBySession[event.sessionId].find((item) => item.id === event.messageId);
        if (message) message.streaming = false;
      }
      if (event.type === "recommendation_cards") {
        this.cardsByMessage[event.messageId] = event.cards || [];
      }
      if (event.type === "confirmation_card") {
        this.cardsByMessage[event.messageId] = [event.card];
        this.pendingConfirmations[event.card.id] = event.card;
        if (event.card.action?.type === "profile") this.openProfileActionDetail(event.card.id);
      }
      if (event.type === "state_delta") {
        const sessions = useSessionsStore();
        const session = sessions.sessions.find((item) => item.id === event.sessionId);
        sessions.patchSession(event.sessionId, {
          title: session?.title === "新对话" ? event.patch?.title : session?.title,
          summary: [session?.summary, event.patch?.summary].filter(Boolean).join(" "),
          turnCount: (session?.turnCount || 0) + (event.patch?.turnCountIncrement || 0),
        });
      }
      if (event.type === "run_error") {
        this.lastError = event.message || "AGUI 响应异常";
        this.streamStatus = "error";
        if (this.timeoutHandle) window.clearTimeout(this.timeoutHandle);
        this.timeoutHandle = null;
        this.abortController = null;
        const message = this.messagesBySession[event.sessionId].find((item) => item.id === event.messageId);
        if (message) {
          message.text = this.lastError;
          message.streaming = false;
        }
      }
      if (event.type === "run_finished") {
        this.streamStatus = "idle";
        this.activeRunId = "";
        if (this.timeoutHandle) window.clearTimeout(this.timeoutHandle);
        this.timeoutHandle = null;
        this.abortController = null;
      }
      this.persist();
    },
    openPersonDetail(personId, context = {}) {
      this.activeDetail = { type: "person", personId };
      this.isDetailSidebarVisible = true;
      reportInteractionEvent({ eventType: "person_detail_open", targetType: "person", targetId: personId, context });
    },
    openContentDetail(contentId, context = {}) {
      this.activeDetail = { type: "content", contentId };
      this.isDetailSidebarVisible = true;
      reportInteractionEvent({ eventType: "content_detail_open", targetType: "content", targetId: contentId, context });
    },
    openProfileActionDetail(cardId) {
      const card = this.pendingConfirmations[cardId];
      this.activeDetail = { type: "profileAction", action: card?.action, cardId };
      this.isDetailSidebarVisible = true;
    },
    openActionDetail(card) {
      if (card.action?.type === "content") this.activeDetail = { type: "contentDraft", draft: card.action.nextContent, cardId: card.id };
      else if (card.action?.type === "review") this.activeDetail = { type: "person", personId: card.action.nextReview.personId, cardId: card.id };
      else this.activeDetail = { type: "profileAction", action: card.action, cardId: card.id };
      this.isDetailSidebarVisible = true;
    },
    closeDetailSidebar() {
      this.isDetailSidebarVisible = false;
    },
    async confirmCard(cardId) {
      const card = this.pendingConfirmations[cardId];
      if (!card || card.status === "confirmed") return;
      const action = card.action;
      if (action.type === "profile") {
        useAuthStore().updateProfile(action.nextProfilePatch || {});
        ElMessage.success("个人主页已更新");
      }
      if (action.type === "review") {
        await useReviewsStore().saveReview(action.nextReview);
        ElMessage.success("评价已保存");
      }
      if (action.type === "content") {
        await useContentStore().saveContent(normalizeContentRecord(action.nextContent));
        ElMessage.success("内容已提交审核");
      }
      action.confirmed = true;
      card.status = "confirmed";
      await reportInteractionEvent({ eventType: `confirm_${action.type}`, targetType: "confirmation_card", targetId: cardId });
      this.persist();
    },
    confirmProfileUpdate(cardId) {
      return this.confirmCard(cardId);
    },
    confirmContentPublish(cardId) {
      return this.confirmCard(cardId);
    },
    confirmReviewSave(cardId) {
      return this.confirmCard(cardId);
    },
    toggleFeedback(target) {
      return reportInteractionEvent({
        eventType: "feedback_toggle",
        targetType: target.targetType,
        targetId: target.targetId,
        value: target.value,
        context: target.context || {},
      });
    },
    cancelCurrentRun() {
      if (this.abortController) this.abortController.abort();
      if (this.timeoutHandle) window.clearTimeout(this.timeoutHandle);
      this.streamStatus = "idle";
      this.activeRunId = "";
      this.abortController = null;
      this.timeoutHandle = null;
      reportInteractionEvent({ eventType: "run_cancelled", targetType: "run" });
    },
    resetSessionState(sessionId) {
      delete this.messagesBySession[sessionId];
      Object.keys(this.cardsByMessage).forEach((messageId) => {
        if (messageId.includes(sessionId)) delete this.cardsByMessage[messageId];
      });
      this.activeDetail = { type: "empty" };
      this.isDetailSidebarVisible = false;
      this.persist();
    },
  },
});
