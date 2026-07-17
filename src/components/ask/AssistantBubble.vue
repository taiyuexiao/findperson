<template>
  <article class="thread-bubble assistant-bubble">
    <span class="thread-role">首问助手</span>
    <p>{{ message.text }}</p>
    <div v-if="message.streaming" class="answer-skeleton"><span></span><span></span><span></span></div>
    <div class="thread-feedback-row">
      <FeedbackButtons :target-key="targetKey" :feedback="feedback" @toggle="handleToggle" />
    </div>
    <div v-if="message.analysis?.tokens?.length" class="thread-tags">
      <span v-for="tag in message.analysis.tokens.slice(0, 6)" :key="tag" class="tag">{{ tag }}</span>
    </div>
  </article>
</template>

<script setup>
import FeedbackButtons from "../common/FeedbackButtons.vue";

defineProps({
  message: { type: Object, required: true },
  feedback: { type: Object, required: true },
  targetKey: { type: String, required: true },
});
const emit = defineEmits(["toggle-feedback"]);

function handleToggle(targetKey, value) {
  emit("toggle-feedback", targetKey, value);
}
</script>
