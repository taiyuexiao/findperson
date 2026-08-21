<template>
  <section class="view active vue-login-shell">
    <div class="login-shell">
      <div class="login-panel">
        <div class="login-brand">
          <span class="brand-mark" aria-hidden="true">
            <img :src="logoUrl" alt="">
          </span>
          <div>
            <h1>欢迎进入首问必答平台</h1>
            <p>支持工号（PXXXX）+ 密码登录。</p>
            <p class="login-demo-hint">示例账号：P0001　密码：swzr2026</p>
          </div>
        </div>
        <el-form class="login-form" :model="form" @submit.prevent>
          <label>
            工号（PXXXX）
            <el-input v-model="form.account" placeholder="请输入工号，如 P0001" />
          </label>
          <label>
            密码
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
          </label>
          <div class="login-actions">
            <el-button class="primary-button" type="primary" @click="login">登录平台</el-button>
            <span role="status">{{ status }}</span>
          </div>
        </el-form>
      </div>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import logoUrl from "../../assets/logo.png";
import { useAuthStore } from "../stores/auth.js";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const form = reactive({ account: "", password: "" });
const status = ref("");

async function login() {
  const result = await auth.login(form);
  if (!result.ok) {
    status.value = result.message;
    return;
  }
  router.push(route.query.redirect || { name: "ask" });
}
</script>
