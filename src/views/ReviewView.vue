<template>
  <section class="view active">
    <div class="page-heading detail-heading">
      <button class="secondary-button back-button" type="button" @click="router.push({ name: 'mine' })">返回</button>
      <div><h1>为他人画像</h1></div>
    </div>
    <el-form class="form-grid" :model="form" @submit.prevent>
      <label>
        评价对象
        <el-select v-model="form.personId">
          <el-option v-for="person in reviewablePeople" :key="person.id" :label="person.name" :value="person.id" />
        </el-select>
      </label>
      <label>评价日期<el-input v-model="form.date" type="date" /></label>
      <label class="wide">他画像评价<el-input v-model="form.text" type="textarea" :rows="5" /></label>
      <div class="form-actions wide">
        <el-button class="primary-button" type="primary" @click="saveReview">提交评价</el-button>
        <el-button class="secondary-button" @click="router.push({ name: 'mine' })">取消</el-button>
        <span role="status">{{ status }}</span>
      </div>
    </el-form>
    <div class="profile-detail review-history-panel">
      <section>
        <h2>已发出的评价</h2>
        <SentReviewList :reviews="reviews.sentReviews" :people="directory.people" @continue="continueReview" @delete="reviews.deleteReview" />
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { currentUserId, getTodayText } from "../state.js";
import SentReviewList from "../components/profile/SentReviewList.vue";
import { useDirectoryStore } from "../stores/directory.js";
import { useReviewsStore } from "../stores/reviews.js";

const router = useRouter();
const directory = useDirectoryStore();
const reviews = useReviewsStore();
const reviewablePeople = computed(() => directory.people.filter((person) => person.id !== currentUserId));
const form = reactive({ personId: reviewablePeople.value[0]?.id || "", date: getTodayText(), text: "", id: "" });
const status = ref("");

async function saveReview() {
  const result = await reviews.saveReview(form);
  status.value = result.ok ? "评价已保存" : result.message;
  if (result.ok) {
    form.id = "";
    form.text = "";
    form.date = getTodayText();
  }
}

function continueReview(review) {
  Object.assign(form, {
    id: review.id,
    personId: review.personId,
    date: review.date,
    text: review.text,
  });
  status.value = "";
}
</script>
