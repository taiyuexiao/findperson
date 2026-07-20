<template>
  <div ref="cloudRef" v-if="tags.length" class="portrait-tag-cloud" :style="cloudStyle" aria-label="他画像事项">
    <span
      v-for="item in packedTags"
      :key="item.tag"
      class="portrait-tag-bubble"
      :style="item.style"
      :title="item.tag"
    >
      {{ item.tag }}
    </span>
  </div>
  <div v-else class="empty-state">{{ emptyText }}</div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

const props = defineProps({
  reviews: { type: Array, required: true },
  availableHeight: { type: Number, default: 126 },
  emptyText: { type: String, default: "暂无他画像。" },
});

const cloudRef = ref(null);
const cloudWidth = ref(440);
let resizeObserver;
const bubblePalette = [
  { background: "rgba(72, 130, 225, 0.42)", text: "#1e4783" },
  { background: "rgba(45, 164, 143, 0.42)", text: "#125950" },
  { background: "rgba(225, 157, 43, 0.42)", text: "#70450f" },
  { background: "rgba(206, 79, 112, 0.40)", text: "#732638" },
  { background: "rgba(112, 85, 200, 0.40)", text: "#433173" },
];

const tags = computed(() => {
  const grouped = new Map();
  props.reviews.forEach((review) => {
    const tag = String(review.tag || "").trim();
    if (!tag) return;
    const entry = grouped.get(tag) || { tag, reviewers: new Set(), latestDate: review.date };
    entry.reviewers.add(review.reviewer);
    if (String(review.date) > String(entry.latestDate)) entry.latestDate = review.date;
    grouped.set(tag, entry);
  });
  return [...grouped.values()]
    .map((entry) => ({ tag: entry.tag, count: entry.reviewers.size, latestDate: entry.latestDate }))
    .sort((left, right) => right.count - left.count || String(right.latestDate).localeCompare(String(left.latestDate)));
});

const layout = computed(() => packBubbles(tags.value, cloudWidth.value, props.availableHeight));
const packedTags = computed(() => layout.value.items);
const cloudStyle = computed(() => ({ height: `${layout.value.height}px` }));

onMounted(() => {
  resizeObserver = new ResizeObserver(([entry]) => {
    const width = Math.round(entry.contentRect.width);
    if (width > 0) cloudWidth.value = width;
  });
  if (cloudRef.value) resizeObserver.observe(cloudRef.value);
});

onBeforeUnmount(() => resizeObserver?.disconnect());

/**
 * A deterministic mini force layout: bubbles repel on contact while a light
 * pull keeps the group compact around its center, similar to a BI bubble view.
 */
function packBubbles(items, availableWidth, availableHeight) {
  const width = Math.max(260, availableWidth || 440);
  const padding = 10;
  const maxCount = Math.max(...items.map((item) => item.count), 1);
  const height = Math.max(54, availableHeight || 126);
  const maxDiameter = Math.min(128, Math.max(36, Math.min(Math.round(width * 0.28), Math.round(height * 0.58))));
  const minDiameter = Math.max(33, Math.round(maxDiameter * 0.5));
  const nodes = items.map((item, index) => {
    const ratio = Math.sqrt(item.count / maxCount);
    const diameter = Math.round(minDiameter + (maxDiameter - minDiameter) * ratio);
    const angle = index * 2.399963229728653;
    const radius = index === 0 ? 0 : (maxDiameter * 0.4 + index * 11);
    return {
      ...item,
      radius: diameter / 2,
      x: width / 2 + Math.cos(angle) * radius,
      y: maxDiameter + 28 + Math.sin(angle) * radius,
    };
  });

  for (let step = 0; step < 220; step += 1) {
    nodes.forEach((node) => {
      node.x += (width / 2 - node.x) * 0.012;
      node.y += (height / 2 - node.y) * 0.012;
    });
    for (let left = 0; left < nodes.length; left += 1) {
      for (let right = left + 1; right < nodes.length; right += 1) {
        const first = nodes[left];
        const second = nodes[right];
        const dx = second.x - first.x || 0.01;
        const dy = second.y - first.y || 0.01;
        const distance = Math.hypot(dx, dy);
        const minimum = first.radius + second.radius + 4;
        if (distance >= minimum) continue;
        const shift = (minimum - distance) / 2;
        first.x -= (dx / distance) * shift;
        first.y -= (dy / distance) * shift;
        second.x += (dx / distance) * shift;
        second.y += (dy / distance) * shift;
      }
    }
    nodes.forEach((node) => {
      node.x = Math.min(width - node.radius - padding, Math.max(node.radius + padding, node.x));
      node.y = Math.min(height - node.radius - padding, Math.max(node.radius + padding, node.y));
    });
  }

  // Final collision-only pass: preserve the compact cluster without allowing
  // the center pull to place labels on top of each other.
  for (let step = 0; step < 180; step += 1) {
    for (let left = 0; left < nodes.length; left += 1) {
      for (let right = left + 1; right < nodes.length; right += 1) {
        const first = nodes[left];
        const second = nodes[right];
        const dx = second.x - first.x || 0.01;
        const dy = second.y - first.y || 0.01;
        const distance = Math.hypot(dx, dy);
        const minimum = first.radius + second.radius + 4;
        if (distance >= minimum) continue;
        const shift = (minimum - distance) / 2;
        first.x -= (dx / distance) * shift;
        first.y -= (dy / distance) * shift;
        second.x += (dx / distance) * shift;
        second.y += (dy / distance) * shift;
      }
    }
    nodes.forEach((node) => {
      node.x = Math.min(width - node.radius - padding, Math.max(node.radius + padding, node.x));
      node.y = Math.min(height - node.radius - padding, Math.max(node.radius + padding, node.y));
    });
  }

  return {
    height,
    items: nodes.map((node, index) => ({
      ...node,
      style: {
        width: `${node.radius * 2}px`,
        height: `${node.radius * 2}px`,
        left: `${node.x - node.radius}px`,
        top: `${node.y - node.radius}px`,
        "--bubble-background": bubblePalette[index % bubblePalette.length].background,
        "--bubble-text": bubblePalette[index % bubblePalette.length].text,
        "--bubble-font-size": `${Math.max(8, Math.min(10, Math.round(node.radius * 0.3)))}px`,
      },
    })),
  };
}
</script>
