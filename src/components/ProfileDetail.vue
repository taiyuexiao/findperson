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
          <button v-if="supervisor" class="supervisor-tag" type="button" @click="$emit('supervisor', supervisor.person.id)">上级：{{ supervisorText }}</button>
          <span v-else class="supervisor-tag">上级：{{ supervisorText }}</span>
        </div>
        <p class="person-meta">联系方式：{{ person.phone || person.contact || "未填写" }}</p>
        <div class="field-row">
          <span v-for="tag in person.domains" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </section>

      <!-- 部门职责：领导展示其负责的部门（多部门搜索框长条 hover 展开），普通成员展示所属部门职责；负责人可编辑 -->
      <section v-if="managedDepartments.length || department" class="profile-block department-responsibility-block">
        <div class="section-row">
          <h2>部门职责</h2>
          <button v-if="canEditResponsibility && !editingResponsibility" class="dept-edit-btn" type="button" @click="startEditResponsibility">编辑</button>
        </div>
        <div v-if="editingResponsibility" class="dept-edit-box">
          <el-input v-model="responsibilityDraft" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="请输入部门职责" />
          <div class="dept-edit-actions">
            <el-button class="primary-button" type="primary" @click="saveResponsibility">保存</el-button>
            <el-button class="secondary-button" @click="cancelEditResponsibility">取消</el-button>
          </div>
        </div>
        <template v-else>
          <template v-if="managedDepartments.length > 1">
            <!-- 长条搜索框样式触发区：鼠标悬浮弹出部门菜单，点击项切换下方卡片 -->
            <el-popover
              trigger="hover"
              placement="bottom-start"
              :width="deptBarWidth"
              :show-arrow="false"
              popper-class="dept-select-popper"
            >
              <template #reference>
                <div ref="deptBarRef" class="dept-select-bar">
                  <el-icon class="dept-select-icon"><Search /></el-icon>
                  <span class="dept-select-value">{{ selectedDepartment.name }}</span>
                  <span class="dept-select-count">等 {{ managedDepartments.length }} 个部门</span>
                  <el-icon class="dept-select-arrow"><ArrowDown /></el-icon>
                </div>
              </template>
              <div class="dept-select-menu">
                <div
                  v-for="d in managedDepartments"
                  :key="d.id"
                  class="dept-select-item"
                  :class="{ 'is-active': d.id === selectedDepartment.id }"
                  @click="selectedDepartmentId = d.id"
                >
                  <span class="dept-select-name">{{ d.name }}</span>
                </div>
              </div>
            </el-popover>
            <!-- 点击后展示对应部门卡片 -->
            <div class="dept-detail-card">
              <div class="section-row"><span class="status-chip status-published">{{ selectedDepartment.name }}</span></div>
              <p>{{ selectedDepartment.responsibility || "该部门暂未维护部门职责说明。" }}</p>
            </div>
          </template>
          <template v-else>
            <div class="section-row"><span class="status-chip status-published">{{ managedDepartments[0]?.name || department?.name }}</span></div>
            <p>{{ managedDepartments[0]?.responsibility || department?.responsibility || "该部门暂未维护部门职责说明。" }}</p>
          </template>
        </template>
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
import { computed, onBeforeUnmount, ref, watchEffect } from 'vue';
import { ArrowDown, Search } from "@element-plus/icons-vue";
import PeerReviewList from "./profile/PeerReviewList.vue";
import { useAuthStore } from "../stores/auth.js";
import { useDirectoryStore } from "../stores/directory.js";

const props = defineProps({
  /** 人员对象 */
  person: Object,
  /** 该人员的发布内容列表 */
  content: Array,
  /** 该人员的评价列表 */
  reviews: Array,
  department: Object,
  supervisor: { type: Object, default: null },
  /** 该人员负责的部门列表(leader_id 匹配) */
  managedDepartments: { type: Array, default: () => [] },
});
defineEmits(['back', 'content', 'supervisor']);

/** 部门路径文本 */
const departmentText = computed(() =>
  props.person.departmentPath?.join(' / ') || props.person.department
);
const supervisorText = computed(() => props.supervisor
  ? `${props.supervisor.department.name} · ${props.supervisor.person.name}`
  : "暂未设置"
);

/** 他画像按事项聚合，并按评价人数和最近评价时间排序。 */
const sortedReviews = computed(() =>
  props.reviews
    .slice()
    .sort((left, right) => String(right.date).localeCompare(String(left.date)))
);

/** 多部门下拉当前选中的部门 id（默认第一个）。 */
const selectedDepartmentId = ref(null);
const selectedDepartment = computed(() =>
  props.managedDepartments.find((d) => d.id === selectedDepartmentId.value)
  || props.managedDepartments[0]
);

const auth = useAuthStore();
const directory = useDirectoryStore();

/** 当前展示的部门（多部门=选中的，单部门=第一个，普通成员=所属部门）。 */
const currentDepartment = computed(() => {
  if (props.managedDepartments.length > 1) return selectedDepartment.value;
  if (props.managedDepartments.length === 1) return props.managedDepartments[0];
  return props.department;
});

/** 仅"科长"（单部门负责人）可编辑部门职责；多部门负责人(科长之上)与普通员工不在此显示编辑入口。 */
const canEditResponsibility = computed(() =>
  props.managedDepartments.length === 1
  && Boolean(currentDepartment.value?.id)
  && currentDepartment.value?.leaderId === auth.userId
);

const editingResponsibility = ref(false);
const responsibilityDraft = ref("");
function startEditResponsibility() {
  responsibilityDraft.value = currentDepartment.value?.responsibility || "";
  editingResponsibility.value = true;
}
async function saveResponsibility() {
  const dept = currentDepartment.value;
  if (!dept) return;
  try {
    await directory.saveDepartmentResponsibility(dept.id, responsibilityDraft.value);
    editingResponsibility.value = false;
  } catch {
    // 保存失败保持编辑态，交由用户重试
  }
}
function cancelEditResponsibility() {
  editingResponsibility.value = false;
}

/** 弹出菜单宽度跟随搜索框长条（动态测量，窗口缩放/人员切换时同步）。 */
const deptBarRef = ref(null);
const deptBarWidth = ref(360);
let resizeObserver = null;
watchEffect(() => {
  const el = deptBarRef.value;
  resizeObserver?.disconnect();
  resizeObserver = null;
  if (!el) return;
  deptBarWidth.value = el.offsetWidth || 360;
  resizeObserver = new ResizeObserver(() => {
    deptBarWidth.value = el.offsetWidth || 360;
  });
  resizeObserver.observe(el);
});
onBeforeUnmount(() => { resizeObserver?.disconnect(); });
</script>

<style scoped>
/* 部门职责：搜索框样式长条触发区 */
.dept-select-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 9px 12px;
  background: #fff;
  color: #303133;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.dept-select-bar:hover {
  border-color: #4a7dff;
  box-shadow: 0 0 0 2px rgba(74, 125, 255, 0.1);
}
.dept-select-icon { color: #a0a7b3; flex-shrink: 0; }
.dept-select-value { font-weight: 600; }
.dept-select-count { color: #a0a7b3; font-size: 13px; flex: 1; }
.dept-select-arrow { color: #a0a7b3; flex-shrink: 0; transition: transform 0.2s; }
.dept-select-bar:hover .dept-select-arrow { transform: rotate(180deg); }

/* 选中部门卡片 */
.dept-detail-card {
  margin-top: 12px;
  border: 1px solid #eef2f7;
  border-radius: 6px;
  padding: 12px 14px;
  background: #fafbfc;
}
.dept-detail-card p { color: #5b6472; }

/* 部门职责编辑 */
.dept-edit-btn {
  border: none;
  background: transparent;
  color: #4a7dff;
  font-size: 13px;
  cursor: pointer;
  padding: 0;
}
.dept-edit-btn:hover { text-decoration: underline; }
.dept-edit-box { margin-top: 4px; }
.dept-edit-actions { display: flex; gap: 8px; margin-top: 8px; }
</style>

<style>
/* 弹出菜单（非 scoped：el-popover 渲染到 body） */
.dept-select-popper { padding: 6px; }
.dept-select-popper .el-popover__title { display: none; }
.dept-select-menu { max-height: 320px; overflow-y: auto; }
.dept-select-item { padding: 10px 12px; border-radius: 4px; cursor: pointer; }
.dept-select-item:hover { background: #f0f4ff; }
.dept-select-item.is-active { background: #eef3ff; }
.dept-select-name { font-weight: 600; color: #303133; }
.dept-select-item.is-active .dept-select-name { color: #4a7dff; }
</style>
