<template>
  <article class="result-card thread-card result-inline is-clickable" tabindex="0" @click="$emit('detail', card.personId)">
    <div class="person-head">
      <div>
        <p class="person-name">{{ card.rank === 1 ? '首推 ' : '' }}{{ card.person.name }}</p>
        <p class="person-meta">{{ departmentText }}</p>
        <p class="person-meta">{{ card.person.role }}</p>
      </div>
      <span class="score-pill">{{ card.rankLabel }}</span>
    </div>
    <div class="field-row">
      <span v-for="tag in card.person.domains" :key="tag" class="tag">{{ tag }}</span>
    </div>
    <ul class="reason-list">
      <li v-for="reason in card.reasons" :key="reason">{{ reason }}</li>
    </ul>
    <p class="person-meta">联系方式：{{ card.person.contact }}</p>
    <div class="card-meta-line" @click.stop>
      <FeedbackButtons :target-key="feedbackKey" :feedback="feedback" @toggle="handleToggleFeedback" />
    </div>
    <div class="related-list" @click.stop>
      <button v-for="item in card.related" :key="item.id" type="button" @click="$emit('content', item.id)">
        {{ item.title }}
      </button>
    </div>
    <el-button class="secondary-button small-button" @click.stop="$emit('profile', card.personId)">查看主页</el-button>
  </article>
</template>

<script setup>
import { computed } from "vue";
import FeedbackButtons from "../common/FeedbackButtons.vue";

const props = defineProps({
  card: { type: Object, required: true },
  feedback: { type: Object, required: true },
  feedbackKey: { type: String, required: true },
});
const departmentText = computed(() => props.card.person.departmentPath?.join(" / ") || props.card.person.department);
const emit = defineEmits(["detail", "content", "profile", "toggle-feedback"]);

function handleToggleFeedback(targetKey, value) {
  emit("toggle-feedback", targetKey, value);
}
</script>
