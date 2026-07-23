<template>
  <section class="view active">
    <div class="page-heading"><div><h1>个人中心</h1></div></div>
    <div v-if="!isEditing" class="profile-detail">
      <ProfileSummary :person="profile" :supervisor="supervisor" @supervisor="openSupervisor">
        <template #actions>
          <el-button class="secondary-button small-button" @click="router.push({ name: 'review' })">为他人画像</el-button>
          <el-button class="primary-button small-button" type="primary" :icon="EditPen" @click="router.push({ name: 'publish' })">发布</el-button>
          <el-button class="secondary-button small-button" @click="startEdit">编辑</el-button>
        </template>
      </ProfileSummary>

      <section v-if="department" class="profile-block department-responsibility-block">
        <div class="content-section-head"><div><h2>部门职责</h2><p class="person-meta">{{ canManageResponsibilities ? '负责部门及下级部门职责' : department.name }}</p></div></div>
        <div v-if="canManageResponsibilities" class="responsibility-manager">
          <div class="responsibility-filter-row">
            <el-select v-model="responsibilityFilter" class="responsibility-filter" clearable placeholder="筛选部门">
              <el-option label="全部负责部门" value="" />
              <el-option v-for="item in responsibilityOptions" :key="item.id" :label="item.path.join(' / ')" :value="item.id" />
            </el-select>
          </div>
          <div class="responsibility-list">
            <article v-for="item in visibleResponsibilities" :key="item.id" class="responsibility-item">
              <div class="responsibility-item-head"><div><h3>{{ item.name }}</h3><p>{{ item.path.join(' / ') }}</p></div><el-button class="secondary-button small-button" @click="startResponsibilityEdit(item)">{{ editingResponsibilityId === item.id ? '取消' : '编辑' }}</el-button></div>
              <template v-if="editingResponsibilityId === item.id">
                <el-input v-model="responsibilityDrafts[item.id]" type="textarea" :rows="3" placeholder="请输入部门职责" />
                <div class="responsibility-item-actions"><el-button class="primary-button small-button" type="primary" @click="saveResponsibility(item)">保存职责</el-button></div>
              </template>
              <p v-else class="responsibility-copy">{{ item.responsibility || '暂未维护部门职责。' }}</p>
            </article>
          </div>
        </div>
        <p v-else>{{ department.responsibility || '暂未维护部门职责。' }}</p>
      </section>

      <div class="portrait-split-grid profile-portrait-split-grid">
        <section class="profile-block self-portrait-block">
          <h2>自画像</h2>
          <p>{{ profile.selfPortrait }}</p>
        </section>
        <section class="profile-block peer-portrait-block">
          <h2>他画像</h2>
          <PeerReviewList :reviews="myPeerReviews" empty-text="暂时还没有收到他画像评价。" />
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
              <span class="status-chip" :class="statusClass(item.status)">{{ item.status }}</span>
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

    <ProfileEditor v-else :form="form" :person="profile" :department="department" :status="status" @cancel="isEditing = false" @save="saveProfile" />
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { EditPen, Search } from "@element-plus/icons-vue";
import PeerReviewList from "../components/profile/PeerReviewList.vue";
import ProfileEditor from "../components/profile/ProfileEditor.vue";
import ProfileSummary from "../components/profile/ProfileSummary.vue";
import { getActiveUserId } from "../state.js";
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
const form = reactive({ contact: "", domainsText: "", selfPortrait: "" });
const profile = computed(() => directory.currentUser);
const supervisor = computed(() => directory.getPersonSupervisor(profile.value?.id));
const department = computed(() => directory.getDepartment(profile.value?.department));
const managedRoots = computed(() => directory.managedDepartments(auth.userId));
const canManageResponsibilities = computed(() => managedRoots.value.length > 0);
const responsibilityFilter = ref("");
const responsibilityDrafts = reactive({});
const responsibilityOptions = computed(() => directory.manageableDepartments(auth.userId));
const visibleResponsibilities = computed(() => responsibilityFilter.value
  ? responsibilityOptions.value.filter((item) => item.id === responsibilityFilter.value)
  : responsibilityOptions.value);
const editingResponsibilityId = ref("");
const myPeerReviews = computed(() => reviews.reviewsForPerson(getActiveUserId()));
watch(visibleResponsibilities, (items) => items.forEach((item) => {
  if (responsibilityDrafts[item.id] === undefined) responsibilityDrafts[item.id] = item.responsibility || "";
}), { immediate: true });
function startEdit() {
  Object.assign(form, {
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

function saveResponsibility(item) {
  directory.updateDepartment(item.id, { responsibility: (responsibilityDrafts[item.id] || "").trim() });
  editingResponsibilityId.value = "";
}

function startResponsibilityEdit(item) {
  if (editingResponsibilityId.value === item.id) {
    editingResponsibilityId.value = "";
    return;
  }
  responsibilityDrafts[item.id] = item.responsibility || "";
  editingResponsibilityId.value = item.id;
}

function toggleSearch() {
  isSearchOpen.value = !isSearchOpen.value;
  if (!isSearchOpen.value) keyword.value = "";
}

function statusClass(status) {
  return status === "已发布" ? "status-published" : status === "待审核" ? "status-pending" : status === "草稿" ? "status-draft" : "status-rejected";
}

function openContent(id) {
  router.push({ name: "contentDetail", params: { id }, query: { from: "mine" } });
}

function openSupervisor(id) {
  router.push({ name: "profile", params: { id }, query: { from: "mine" } });
}

async function deleteContent(id) {
  await content.deleteContent(id);
}
</script>
