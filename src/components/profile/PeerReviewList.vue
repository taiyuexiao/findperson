<template>
  <div v-if="portraitTags.length" class="portrait-tag-list" aria-label="他画像事项">
    <span
      v-for="item in portraitTags"
      :key="item.tag"
      class="portrait-tag"
      :title="`${item.tag}：${item.count}`"
    >
      {{ item.tag }}：{{ item.count }}
    </span>
  </div>
  <div v-else class="empty-state">{{ emptyText }}</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  reviews: { type: Array, required: true },
  emptyText: { type: String, default: "暂无他画像。" },
});

const portraitTags = computed(() => {
  const grouped = new Map();
  props.reviews.forEach((review) => {
    const tag = String(review.tag || "").trim();
    if (!tag) return;
    const entry = grouped.get(tag) || { tag, count: 0, latestDate: review.date };
    entry.count += 1;
    if (String(review.date) > String(entry.latestDate)) entry.latestDate = review.date;
    grouped.set(tag, entry);
  });
  return [...grouped.values()]
    .sort((left, right) => right.count - left.count || String(right.latestDate).localeCompare(String(left.latestDate)));
});
</script>
