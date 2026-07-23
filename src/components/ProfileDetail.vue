<!-- 人员主页：展示姓名、部门、岗位、自画像、他画像、发布内容 -->
<template>
  <div class="profile-page-stack">
    <div class="page-heading detail-heading">
      <button class="secondary-button back-button" @click="$emit('back')">返回</button>
      <div><h1>人员主页</h1></div>
    </div>
    <div class="profile-detail">

      <!-- 基本信息区 -->
      <section class="profile-block profile-header-block">
        <div class="profile-name-row">
          <h2>{{ person.name }}</h2>
          <div class="profile-actions"></div>
        </div>
        <div class="profile-info-chain">
          <span class="chain-item">{{ departmentText }}</span>
          <span class="chain-dot"></span>
          <span class="chain-item">{{ person.role }}</span>
        </div>
        <p class="person-meta">联系方式：{{ person.contact }}</p>
        <div class="field-row">
          <span v-for="tag in person.domains" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </section>

      <!-- 自画像 + 他画像 -->
      <div class="portrait-split-grid profile-portrait-split-grid">
        <section class="profile-block self-portrait-block">
          <h2>自画像</h2>
          <p>{{ person.selfPortrait }}</p>
        </section>
        <section class="profile-block peer-portrait-block">
          <h2>他画像</h2>
          <PeerReviewList :reviews="sortedReviews" />
        </section>
      </div>

      <!-- 发布内容 -->
      <section class="profile-block">
        <h2>发布内容</h2>
        <div class="content-card-grid">
          <article
            v-for="item in content"
            :key="item.id"
            class="content-mini-card clickable-card"
            @click="$emit('content', item.id)"
          >
            <div class="content-mini-head">
              <h3>{{ item.title }}</h3>
              <span v-if="item.pinned" class="pin-badge">置顶</span>
            </div>
            <p>{{ item.summary }}</p>
            <div class="field-row">
              <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </article>
          <div v-if="!content.length" class="empty-state">暂无发布内容。</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import PeerReviewList from "./profile/PeerReviewList.vue";

const props = defineProps({
  /** 人员对象 */
  person: Object,
  /** 该人员的发布内容列表 */
  content: Array,
  /** 该人员的评价列表 */
  reviews: Array,
});
defineEmits(['back', 'content']);

/** 部门路径文本 */
const departmentText = computed(() =>
  props.person.departmentPath?.join(' / ') || props.person.department
);

/** 他画像按事项聚合，并按评价人数和最近评价时间排序。 */
const sortedReviews = computed(() =>
  props.reviews
    .slice()
    .sort((left, right) => String(right.date).localeCompare(String(left.date)))
);
</script>
