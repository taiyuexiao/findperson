<template>
  <aside class="sidebar">
    <div class="brand">
      <span class="brand-mark" aria-hidden="true">
        <img :src="logoUrl" alt="">
      </span>
      <div>
        <strong>首问责任平台</strong>
        <span>展示型交互 Demo</span>
      </div>
    </div>
    <nav class="sidebar-nav" aria-label="页面导航">
      <RouterLink v-for="item in visibleNavItems" :key="item.name" :to="{ name: item.name }" custom v-slot="{ href, navigate, isActive }">
        <a class="nav-button" :class="{ active: isActive }" :href="href" @click="navigate">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </a>
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup>
import { computed } from "vue";
import { ChatDotRound, Collection, DataAnalysis } from "@element-plus/icons-vue";
import logoUrl from "../../../assets/logo.png";
import { useAuthStore } from "../../stores/auth.js";

const navItems = [
  { name: "ask", label: "智能问答", icon: ChatDotRound },
  { name: "directory", label: "名片库", icon: Collection },
  { name: "admin", label: "后台管理", icon: DataAnalysis },
];
const auth = useAuthStore();
const visibleNavItems = computed(() => navItems.filter((item) => item.name !== "admin" || auth.isAdmin));
</script>
