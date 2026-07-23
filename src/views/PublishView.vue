<template>
  <section class="view active">
    <div class="page-heading detail-heading">
      <button class="secondary-button back-button" type="button" @click="goBack">返回</button>
      <div><h1>内容发布</h1></div>
    </div>
    <div class="publish-layout">
      <ContentForm :form="form" :publisher="auth.displayName" :status="status" @save="saveContent" @delete="deleteCurrent" />
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth.js";
import ContentForm from "../components/content/ContentForm.vue";
import { useContentStore } from "../stores/content.js";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const content = useContentStore();
const status = ref("");
const form = reactive({ editingId: "", title: "", tagsText: "", summary: "", body: "" });

onMounted(() => {
  if (route.query.id) {
    const item = content.getContent(route.query.id);
    if (item && content.isOwnContent(item)) {
      Object.assign(form, {
        editingId: item.id,
        title: item.title,
        tagsText: item.tags.join("、"),
        summary: item.summary,
        body: item.body,
      });
    }
  }
  if (route.query.draft) {
    try {
      const draft = JSON.parse(decodeURIComponent(route.query.draft));
      Object.assign(form, {
        editingId: "",
        title: draft.title || "",
        tagsText: (draft.tags || []).join("、"),
        summary: draft.summary || "",
        body: draft.body || "",
      });
    } catch {
      // Ignore malformed draft query; user can fill manually.
    }
  }
});

async function saveContent(mode = "submit") {
  if (!form.title.trim() || (mode === "submit" && (!form.summary.trim() || !form.body.trim()))) {
    status.value = "请补齐标题、摘要和正文";
    return;
  }
  const record = await content.saveContent(form, mode);
  status.value = mode === "draft" ? "草稿已保存" : (form.editingId ? "修改已提交审核" : "内容已提交审核");
  form.editingId = record.id;
}

async function deleteCurrent() {
  if (await content.deleteContent(form.editingId)) router.push({ name: "mine" });
}

function goBack() {
  if (route.query.from === "ask") router.push({ name: "ask" });
  else router.push({ name: "mine" });
}
</script>
