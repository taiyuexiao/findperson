<template>
  <div v-if="cards.length" class="inline-card-group">
    <div class="inline-group-title">
      <span class="soft-count">{{ cards.length }} 位推荐对象</span>
      <strong>推荐人员卡片</strong>
      <span class="soft-count">单击看详情，双击进主页</span>
    </div>
    <div class="inline-card-rail">
      <RecommendationCard
        v-for="card in cards"
        :key="card.id"
        :card="card"
        @profile="$emit('profile', $event)"
        @detail="$emit('detail', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import RecommendationCard from "./RecommendationCard.vue";

defineProps({
  cards: { type: Array, required: true },
});
defineEmits(["profile", "detail"]);
</script>
