<template>
  <section class="view active">
    <div class="page-heading"><div><h1>名片库</h1></div></div>
    <div class="toolbar">
      <div class="search-field">
        <el-icon><Search /></el-icon>
        <el-input v-model="directory.keyword" placeholder="搜索关键词、人员、职责" clearable />
      </div>
      <DepartmentFilter
        :filters="directory.filters"
        :level1-options="directory.level1Options"
        :level2-options="directory.level2Options"
        :level3-options="directory.level3Options"
        @change="handleDepartmentChange"
      />
    </div>
    <div class="card-grid">
      <PersonCard v-for="person in directory.filteredPeople" :key="person.id" :person="person" @open="openProfile" />
      <div v-if="!directory.filteredPeople.length" class="empty-state">没有匹配到人员名片。</div>
    </div>
  </section>
</template>

<script setup>
import { Search } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import DepartmentFilter from "../components/directory/DepartmentFilter.vue";
import PersonCard from "../components/directory/PersonCard.vue";
import { useDirectoryStore } from "../stores/directory.js";

const router = useRouter();
const directory = useDirectoryStore();

function openProfile(id) {
  router.push({ name: "profile", params: { id }, query: { from: "directory" } });
}

function handleDepartmentChange(key) {
  if (key === "level1") directory.resetDepartmentLevel(1);
  if (key === "level2") directory.resetDepartmentLevel(2);
}
</script>
