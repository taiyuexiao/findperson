<template>
  <section class="view active">
    <div class="page-heading detail-heading">
      <button class="secondary-button back-button" type="button" @click="goBack">返回</button>
      <div><h1>内容详情</h1></div>
    </div>
    <article v-if="item" class="content-detail content-detail-single">
      <div class="content-detail-head-single">
        <div class="content-hit-head">
          <div>
            <h1>{{ item.title }}</h1>
            <p class="content-detail-owner">{{ owner?.name || '未知发布人' }} · {{ item.publishedAt }}</p>
          </div>
          <span v-if="item.pinned" class="pin-badge">置顶</span>
        </div>
        <div class="field-row">
          <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </div>
      <div class="content-body content-body-merged">
        <h3>摘要</h3>
        <p>{{ item.summary }}</p>
        <h3>正文</h3>
        <p class="content-body-plain">{{ item.body }}</p>
      </div>
      <div v-if="content.isOwnContent(item)" class="content-hit-actions">
        <el-button class="secondary-button small-button" @click="content.toggleContentPin(item.id)">
          {{ item.pinned ? '取消置顶' : '置顶' }}
        </el-button>
      </div>
    </article>
    <div v-else class="empty-state">没有找到内容。</div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useContentStore } from "../stores/content.js";
import { useDirectoryStore } from "../stores/directory.js";

const route = useRoute();
const router = useRouter();
const content = useContentStore();
const directory = useDirectoryStore();
const item = computed(() => content.getContent(route.params.id));
const owner = computed(() => directory.getPerson(item.value?.ownerId));

function goBack() {
  if (route.query.from === "ask") router.push({ name: "ask" });
  else if (route.query.from === "profile" && route.query.personId) router.push({ name: "profile", params: { id: route.query.personId } });
  else router.push({ name: "mine" });
}
</script>
