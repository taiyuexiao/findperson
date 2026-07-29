<template>
  <section class="view active" id="view-ask">
    <div
      class="ask-workspace"
      :class="{
        'has-session': agui.activeMessages.length,
        'has-detail': agui.isDetailSidebarVisible,
        'detail-collapsed': !agui.isDetailSidebarVisible
      }"
    >
      <ConversationSidebar
        v-model:search="historySearch"
        :sessions="sessions.sessions"
        :searched-sessions="searchedSessions"
        :active-session-id="sessions.activeSessionId"
        :is-search-open="isHistorySearchOpen"
        @toggle-search="isHistorySearchOpen = !isHistorySearchOpen"
        @close-search="isHistorySearchOpen = false"
        @new-chat="newChat"
        @select="selectSession"
        @command="handleSessionCommand"
      />

      <section class="chat-shell" :class="{ 'has-session': agui.activeMessages.length, 'is-loading': agui.isStreaming }">
        <div class="chat-topbar">
          <div><h1>智能问答</h1></div>
          <el-button class="topbar-icon-button ask-detail-toggle" @click="agui.isDetailSidebarVisible = !agui.isDetailSidebarVisible">
            <el-icon><Memo /></el-icon>
          </el-button>
        </div>

        <div class="chat-main">
          <div v-if="!agui.activeMessages.length && !agui.isStreaming" class="chat-hero">
            <div class="sample-row home-samples" aria-label="示例问题">
              <div class="chat-entry-title">开始对话</div>
            </div>
          </div>
          <div class="chat-thread-panel">
            <ThreadList>
              <ThreadTurn v-for="turn in turns" :key="turn.user.id">
                <article class="thread-bubble user-bubble">
                  <p>{{ turn.user.text }}</p>
                </article>
                <AssistantBubble
                  :message="turn.assistant"
                  :feedback="feedback.feedbackMap"
                  :target-key="`answer:${turn.assistant.id}`"
                  @toggle-feedback="toggleFeedback"
                />

                <RecommendationCardGroup
                  :cards="recommendationCards(turn.assistant.id)"
                  :feedback="feedback.feedbackMap"
                  :message-id="turn.assistant.id"
                  @detail="(personId) => agui.openPersonDetail(personId, { sessionId: sessions.activeSessionId, messageId: turn.assistant.id })"
                  @content="(contentId) => agui.openContentDetail(contentId, { source: 'ask' })"
                  @profile="openProfile"
                  @toggle-feedback="toggleFeedback"
                />

                <ActionCard
                  v-for="card in confirmationCards(turn.assistant.id)"
                  :key="card.id"
                  :card="card"
                  :people="directory.people"
                  :latest="true"
                  @confirm="agui.confirmCard"
                  @edit="continueActionDraft"
                  @publish="startPublishDraft"
                  @profile="openProfile"
                  @content="openContentDetail"
                  @detail="agui.openActionDetail"
                />
              </ThreadTurn>
            </ThreadList>
          </div>
        </div>

        <ChatComposer v-model="questionInput" :disabled="agui.isStreaming" @send="sendQuestion" />
      </section>

      <DetailSidebar
        :visible="agui.isDetailSidebarVisible"
        :detail="agui.activeDetail"
        :people="directory.people"
        :content="content.publicContentRecords"
        :feedback="feedback.feedbackMap"
        :current-user-id="auth.userId"
        @close="agui.closeDetailSidebar"
        @profile="openProfile"
        @content="openContentDetail"
        @mine="continueDetailAction"
        @confirm-profile="confirmProfileFromDetail"
        @toggle-feedback="toggleFeedback"
      />
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessageBox } from "element-plus";
import { Memo } from "@element-plus/icons-vue";
import ActionCard from "../components/ask/ActionCard.vue";
import AssistantBubble from "../components/ask/AssistantBubble.vue";
import ChatComposer from "../components/ask/ChatComposer.vue";
import ConversationSidebar from "../components/ask/ConversationSidebar.vue";
import DetailSidebar from "../components/ask/DetailSidebar.vue";
import RecommendationCardGroup from "../components/ask/RecommendationCardGroup.vue";
import ThreadList from "../components/ask/ThreadList.vue";
import ThreadTurn from "../components/ask/ThreadTurn.vue";
import { useAguiStore } from "../stores/agui.js";
import { useAuthStore } from "../stores/auth.js";
import { useContentStore } from "../stores/content.js";
import { useDirectoryStore } from "../stores/directory.js";
import { useFeedbackStore } from "../stores/feedback.js";
import { useSessionsStore } from "../stores/sessions.js";
import { useDraftsStore } from "../stores/drafts.js";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const sessions = useSessionsStore();
const agui = useAguiStore();
const directory = useDirectoryStore();
const content = useContentStore();
const feedback = useFeedbackStore();
const drafts = useDraftsStore();

sessions.init();
sessions.ensureActiveSession();

const questionInput = ref("");
const historySearch = ref("");
const isHistorySearchOpen = ref(false);
const searchedSessions = computed(() => sessions.searchSessions(historySearch.value));
const turns = computed(() => {
  const messages = agui.activeMessages;
  const pairs = [];
  for (let index = 0; index < messages.length; index += 2) {
    if (messages[index]?.role === "user" && messages[index + 1]?.role === "assistant") {
      pairs.push({ user: messages[index], assistant: messages[index + 1] });
    }
  }
  return pairs;
});

function recommendationCards(messageId) {
  return (agui.cardsByMessage[messageId] || []).filter((card) => card.kind === "recommendation");
}

function confirmationCards(messageId) {
  return (agui.cardsByMessage[messageId] || []).filter((card) => card.kind === "confirmation");
}

function newChat() {
  sessions.createOrReuseBlankSession();
}

function selectSession(id) {
  sessions.selectSession(id);
  isHistorySearchOpen.value = false;
}

async function handleSessionCommand(command, sessionId) {
  if (command === "rename") {
    try {
      const session = sessions.sessions.find((item) => item.id === sessionId);
      const { value } = await ElMessageBox.prompt("请输入新的会话标题", "重命名会话", {
        confirmButtonText: "确认",
        cancelButtonText: "取消",
        inputValue: session?.title || "新对话",
      });
      sessions.renameSession(sessionId, value);
    } catch {
      return;
    }
  }
  if (command === "delete") sessions.deleteSession(sessionId);
}

async function sendQuestion() {
  const question = questionInput.value.trim();
  if (!question) return;
  const session = sessions.ensureActiveSession();
  questionInput.value = "";
  await agui.sendMessage(session.id, question);
}

function toggleFeedback(targetKey, value) {
  feedback.toggle(targetKey, value, { sessionId: sessions.activeSessionId });
}

function openProfile(personId) {
  router.push({ name: "profile", params: { id: personId }, query: { redirect: route.fullPath } });
}

function openContentDetail(contentId) {
  router.push({ name: "contentDetail", params: { id: contentId }, query: { redirect: route.fullPath } });
}

function startPublishDraft(draft) {
  const draftId = drafts.create("content", draft || {}, route.fullPath);
  router.push({
    name: "publish",
    query: { draftId, redirect: route.fullPath },
  });
}

function continueActionDraft(action) {
  if (action.type === "profile") {
    const draftId = drafts.create("profile", action.nextProfilePatch || {}, route.fullPath);
    router.push({ name: "mine", query: { edit: "profile", draftId, redirect: route.fullPath } });
  } else if (action.type === "review") {
    const draftId = drafts.create("review", action.nextReview || {}, route.fullPath);
    router.push({ name: "review", query: { draftId, redirect: route.fullPath } });
  }
}

function continueDetailAction() {
  if (agui.activeDetail.type === "profileAction") continueActionDraft(agui.activeDetail.action || {});
  else if (agui.activeDetail.type === "contentDraft") startPublishDraft(agui.activeDetail.draft);
  else router.push({ name: "mine", query: { redirect: route.fullPath } });
}

function confirmProfileFromDetail() {
  const cardId = agui.activeDetail.cardId;
  if (cardId) agui.confirmCard(cardId);
}
</script>
