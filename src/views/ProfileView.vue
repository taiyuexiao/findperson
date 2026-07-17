<template>
  <section class="view active">
    <ProfileDetail
      v-if="person"
      :person="person"
      :content="content.contentByOwner(person.id)"
      :reviews="reviews.reviewsForPerson(person.id)"
      @back="goBack"
      @content="openContent"
    />
    <div v-else class="empty-state">没有找到该人员主页。</div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import ProfileDetail from "../components/ProfileDetail.vue";
import { useContentStore } from "../stores/content.js";
import { useDirectoryStore } from "../stores/directory.js";
import { useReviewsStore } from "../stores/reviews.js";

const route = useRoute();
const router = useRouter();
const directory = useDirectoryStore();
const content = useContentStore();
const reviews = useReviewsStore();
const person = computed(() => directory.getPerson(route.params.id));

function goBack() {
  if (route.query.from === "ask") router.push({ name: "ask" });
  else router.push({ name: "directory" });
}

function openContent(id) {
  router.push({ name: "contentDetail", params: { id }, query: { from: "profile", personId: route.params.id } });
}
</script>
