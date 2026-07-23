<template>
  <section class="view active">
    <div class="page-heading detail-heading">
      <button class="secondary-button back-button" type="button" @click="router.push({ name: 'mine' })">返回</button>
      <div><h1>为他人画像</h1></div>
    </div>
    <el-form class="form-grid" :model="form" @submit.prevent>
      <label>
        同事
        <el-select v-model="form.personId">
          <el-option v-for="person in reviewablePeople" :key="person.id" :label="person.name" :value="person.id" />
        </el-select>
      </label>
      <label>日期<el-input v-model="form.date" type="date" /></label>
      <label class="wide">
        事项
        <el-select v-model="form.tag" filterable placeholder="搜索或选择事项">
          <el-option v-for="item in personTags" :key="item.tag" :label="item.tag" :value="item.tag" />
          <el-option label="其他" :value="OTHER_TAG" />
        </el-select>
      </label>
      <label v-if="form.tag === OTHER_TAG" class="wide">
        填写事项
        <el-input v-model="form.customTag" maxlength="20" show-word-limit placeholder="请输入事项" />
      </label>
      <div class="form-actions wide">
        <el-button class="primary-button" type="primary" @click="saveReview">添加事项</el-button>
        <el-button class="secondary-button" @click="router.push({ name: 'mine' })">取消</el-button>
        <span role="status">{{ status }}</span>
      </div>
    </el-form>
    <div class="profile-detail review-history-panel">
      <section>
        <h2>我添加的事项</h2>
        <SentReviewList :reviews="reviews.sentReviews" :people="directory.people" @continue="continueReview" @delete="reviews.deleteReview" />
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { getActiveUserId, getTodayText } from "../state.js";
import SentReviewList from "../components/profile/SentReviewList.vue";
import { useDirectoryStore } from "../stores/directory.js";
import { useReviewsStore } from "../stores/reviews.js";

const router = useRouter();
const directory = useDirectoryStore();
const reviews = useReviewsStore();
const reviewablePeople = computed(() => directory.people.filter((person) => person.id !== getActiveUserId()));
const OTHER_TAG = "__other__";
const form = reactive({ personId: reviewablePeople.value[0]?.id || "", date: getTodayText(), tag: "", customTag: "", id: "" });
const status = ref("");
const personTags = computed(() => {
  const person = directory.getPerson(form.personId);
  const selfTags = (person?.domains || []).map((tag) => ({ tag }));
  const existingTags = reviews.tagsForPerson(form.personId)
    .filter((item) => !selfTags.some((selfTag) => selfTag.tag === item.tag));
  return [...selfTags, ...existingTags];
});

watch(() => form.personId, () => {
  form.tag = "";
  form.customTag = "";
});

async function saveReview() {
  const tag = form.tag === OTHER_TAG ? form.customTag : form.tag;
  const result = await reviews.saveReview({ ...form, tag });
  status.value = result.ok ? "事项已添加" : result.message;
  if (result.ok) {
    form.id = "";
    form.tag = "";
    form.customTag = "";
    form.date = getTodayText();
  }
}

function continueReview(review) {
  Object.assign(form, {
    id: review.id,
    personId: review.personId,
    date: review.date,
    tag: reviews.tagFor(review),
    customTag: "",
  });
  status.value = "";
}
</script>
