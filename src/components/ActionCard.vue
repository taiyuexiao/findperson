<!-- 操作卡片：用于问答页中资料维护、评价、内容发布等待确认动作 -->
<template>

  <!-- ── 资料维护 ── -->
  <article
    v-if="action.type === 'profile'"
    :class="['thread-card', 'action-card', latest ? 'is-pending' : '', 'is-clickable']"
    @click="$emit('detail', card || { type: 'profileAction', action })"
  >
    <div class="thread-card-head">
      <span class="intent-pill">{{ analysis.intent }}</span>
      <strong>{{ action.title }}</strong>
    </div>
    <p>{{ action.description }}</p>
    <div class="action-preview">
      <span v-for="item in (action.changes?.length ? action.changes : ['未识别到明确字段，将引导进入个人中心编辑。'])" :key="item">
        {{ item }}
      </span>
    </div>
    <div class="thread-card-actions" @click.stop>
      <button v-if="isConfirmed" class="secondary-button small-button" @click="$emit('edit', action)">继续编辑</button>
      <button v-else-if="hasProfilePatch" class="primary-button small-button" @click="$emit('confirm', confirmKey)">确认更新主页</button>
      <button v-if="!isConfirmed" class="secondary-button small-button" @click="$emit('edit', action)">手动编辑</button>
    </div>
  </article>

  <!-- ── 他人评价 ── -->
  <article
    v-else-if="action.type === 'review'"
    :class="['thread-card', 'action-card', latest ? 'is-pending' : '', 'is-clickable']"
    @click="$emit('detail', card || { type: 'person', personId: action.nextReview.personId })"
  >
    <div class="thread-card-head">
      <span class="intent-pill">{{ analysis.intent }}</span>
      <strong>{{ action.title }}</strong>
    </div>
    <p>{{ action.description }}</p>
    <div class="publish-preview">
      <strong>{{ reviewPerson?.name || '待确认人员' }}</strong>
      <span>{{ action.nextReview.date }}</span>
      <p>{{ action.nextReview.text }}</p>
    </div>
    <div class="thread-card-actions" @click.stop>
      <button v-if="isConfirmed" class="primary-button small-button" @click="$emit('profile', action.nextReview.personId)">
        查看评价对象
      </button>
      <button v-else class="primary-button small-button" @click="$emit('confirm', confirmKey)">确认保存评价</button>
      <button class="secondary-button small-button" @click="$emit('edit', action)">
        {{ isConfirmed ? '继续补充' : '继续修改' }}
      </button>
    </div>
  </article>

  <!-- ── 内容发布（默认） ── -->
  <article
    v-else
    :class="['thread-card', 'action-card', latest ? 'is-pending' : '', 'is-clickable']"
    @click="$emit('detail', isConfirmed
      ? { type: 'content', contentId: action.nextContent.id }
      : (card || { type: 'contentDraft', draft: action.nextContent })
    )"
  >
    <div class="thread-card-head">
      <span class="intent-pill">{{ analysis.intent }}</span>
      <strong>{{ action.title }}</strong>
    </div>
    <p>{{ action.description }}</p>
    <div class="publish-preview">
      <strong>{{ action.nextContent.title }}</strong>
      <span>{{ action.nextContent.tags.join('、') }}</span>
      <p>{{ action.nextContent.summary }}</p>
    </div>
    <div class="thread-card-actions" @click.stop>
      <button v-if="isConfirmed" class="primary-button small-button" @click="$emit('content', action.nextContent.id)">
        查看内容
      </button>
      <button v-else class="primary-button small-button" @click="$emit('confirm', confirmKey)">确认发布</button>
      <button class="secondary-button small-button" @click="$emit('publish', action.nextContent)">
        {{ isConfirmed ? '继续编辑' : '手动补充' }}
      </button>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  /** 问答匹配结果对象 */
  result: Object,
  /** AGUI confirmation card */
  card: Object,
  /** 全部人员列表 */
  people: Array,
  /** 是否为最新一轮对话 */
  latest: Boolean,
});
defineEmits(['confirm', 'edit', 'publish', 'profile', 'content', 'detail']);

const action = computed(() => props.card?.action || props.result?.action || {});
const analysis = computed(() => props.card?.analysis || props.result?.analysis || {});
const isConfirmed = computed(() => action.value.confirmed || props.card?.status === 'confirmed');
const confirmKey = computed(() => props.card?.id || action.value.type);
const hasProfilePatch = computed(() => Object.keys(action.value.nextProfilePatch || {}).length > 0);

/** 评价对象的人员信息 */
const reviewPerson = computed(() => {
  if (action.value.type !== 'review') return null;
  return props.people.find((item) => item.id === action.value.nextReview.personId);
});
</script>
