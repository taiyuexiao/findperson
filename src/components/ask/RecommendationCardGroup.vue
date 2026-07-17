<template>
  <div v-if="cards.length" class="inline-card-group">
    <div class="inline-group-title">
      <span class="soft-count">{{ cards.length }} 位推荐对象</span>
      <strong>推荐人员卡片</strong>
    </div>
    <div class="inline-card-rail">
      <RecommendationCard
        v-for="card in cards"
        :key="card.id"
        :card="card"
        :feedback="feedback"
        :feedback-key="`person:${messageId}:${card.personId}`"
        @detail="$emit('detail', $event)"
        @content="$emit('content', $event)"
        @profile="$emit('profile', $event)"
        @toggle-feedback="(...args) => $emit('toggle-feedback', ...args)"
      />
    </div>
  </div>
</template>

<script setup>
import RecommendationCard from "./RecommendationCard.vue";

defineProps({
  cards: { type: Array, required: true },
  feedback: { type: Object, required: true },
  messageId: { type: String, required: true },
});
defineEmits(["detail", "content", "profile", "toggle-feedback"]);
</script>
