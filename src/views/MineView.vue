<template>
  <section class="view active">
    <div class="page-heading"><div><h1>个人中心</h1></div></div>
    <div v-if="!isEditing" class="profile-detail">
      <ProfileSummary :person="profile">
        <template #actions>
          <el-button class="secondary-button small-button" @click="startEdit">编辑</el-button>
          <el-button class="secondary-button small-button" @click="router.push({ name: 'review' })">为他人画像</el-button>
          <el-button class="primary-button small-button" type="primary" @click="router.push({ name: 'publish' })">发布</el-button>
        </template>
      </ProfileSummary>

      <div class="portrait-split-grid profile-portrait-split-grid">
        <section ref="selfPortraitRef" class="profile-block self-portrait-block">
          <h2>自画像</h2>
          <p>{{ profile.selfPortrait }}</p>
        </section>
        <section class="profile-block peer-portrait-block" :style="{ height: `${peerPortraitHeight}px` }">
          <h2>他画像</h2>
          <PeerReviewList :reviews="myPeerReviews" :available-height="peerCloudHeight" empty-text="暂时还没有收到他画像评价。" />
        </section>
      </div>

      <section class="profile-block">
        <div class="content-section-head">
          <h2>发布内容</h2>
          <el-button class="secondary-button small-button" @click="toggleSearch">{{ isSearchOpen ? '收起搜索' : '搜索' }}</el-button>
        </div>
        <div v-if="isSearchOpen" class="search-field mine-search-field mine-search-bar">
          <el-icon><Search /></el-icon>
          <el-input v-model="keyword" placeholder="搜索本人发布内容" clearable />
        </div>
        <div class="content-card-grid">
          <article v-for="item in content.filteredMyContent(keyword)" :key="item.id" class="content-mini-card clickable-card" @click="openContent(item.id)">
            <div class="content-mini-head">
              <h3>{{ item.title }}</h3>
              <span v-if="item.pinned" class="pin-badge">置顶</span>
            </div>
            <p>{{ item.summary }}</p>
            <div class="field-row">
              <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
            <div class="content-mini-actions" @click.stop>
              <el-button class="secondary-button small-button" @click="router.push({ name: 'publish', query: { id: item.id } })">编辑</el-button>
              <el-button class="secondary-button small-button" @click="deleteContent(item.id)">删除</el-button>
              <el-button class="secondary-button small-button" @click="content.toggleContentPin(item.id)">{{ item.pinned ? '取消置顶' : '置顶' }}</el-button>
            </div>
          </article>
          <div v-if="!content.filteredMyContent(keyword).length" class="empty-state">暂时还没有匹配的本人发布内容。</div>
        </div>
      </section>
    </div>

    <ProfileEditor v-else :form="form" :status="status" @cancel="isEditing = false" @save="saveProfile" />
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { Search } from "@element-plus/icons-vue";
import PeerReviewList from "../components/profile/PeerReviewList.vue";
import ProfileEditor from "../components/profile/ProfileEditor.vue";
import ProfileSummary from "../components/profile/ProfileSummary.vue";
import { currentUserId } from "../state.js";
import { useAuthStore } from "../stores/auth.js";
import { useContentStore } from "../stores/content.js";
import { useDirectoryStore } from "../stores/directory.js";
import { useReviewsStore } from "../stores/reviews.js";

const router = useRouter();
const auth = useAuthStore();
const directory = useDirectoryStore();
const content = useContentStore();
const reviews = useReviewsStore();
const isEditing = ref(false);
const isSearchOpen = ref(false);
const keyword = ref("");
const status = ref("");
const form = reactive({ name: "", department: "", role: "", contact: "", domainsText: "", selfPortrait: "" });
const profile = computed(() => directory.currentUser);
const myPeerReviews = computed(() => reviews.reviewsForPerson(currentUserId));
const selfPortraitRef = ref(null);
const peerPortraitHeight = ref(350);
let selfPortraitObserver;
const peerCloudHeight = computed(() => Math.max(54, peerPortraitHeight.value - 56));

function observeSelfPortrait() {
  selfPortraitObserver?.disconnect();
  if (!selfPortraitRef.value) return;
  selfPortraitObserver = new ResizeObserver(() => {
    peerPortraitHeight.value = Math.max(350, Math.ceil(selfPortraitRef.value?.getBoundingClientRect().height || 0));
  });
  selfPortraitObserver.observe(selfPortraitRef.value);
}

onMounted(observeSelfPortrait);
onBeforeUnmount(() => selfPortraitObserver?.disconnect());
watch(isEditing, async (editing) => {
  if (!editing) {
    await nextTick();
    observeSelfPortrait();
  }
});

function startEdit() {
  Object.assign(form, {
    name: profile.value.name,
    department: profile.value.department,
    role: profile.value.role,
    contact: profile.value.contact,
    domainsText: profile.value.domains.join("、"),
    selfPortrait: profile.value.selfPortrait,
  });
  status.value = "";
  isEditing.value = true;
}

function saveProfile() {
  auth.updateProfile(form);
  status.value = "已保存";
  isEditing.value = false;
}

function toggleSearch() {
  isSearchOpen.value = !isSearchOpen.value;
  if (!isSearchOpen.value) keyword.value = "";
}

function openContent(id) {
  router.push({ name: "contentDetail", params: { id }, query: { from: "mine" } });
}

async function deleteContent(id) {
  await content.deleteContent(id);
}
</script>
