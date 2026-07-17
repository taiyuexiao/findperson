<template>
  <ul v-if="reviews.length" class="peer-review-list">
    <li v-for="review in reviews" :key="review.id">
      {{ review.text }}（{{ review.reviewer }} · {{ review.date }}）
    </li>
  </ul>
  <div v-else class="empty-state">{{ emptyText }}</div>
</template>

<script setup>
defineProps({
  reviews: { type: Array, required: true },
  emptyText: { type: String, default: "暂无评价。" },
});
</script>
