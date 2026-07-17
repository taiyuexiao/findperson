<template>
  <section class="view active vue-login-shell">
    <div class="login-shell">
      <div class="login-panel">
        <div class="login-brand">
          <span class="brand-mark" aria-hidden="true">
            <img :src="logoUrl" alt="">
          </span>
          <div>
            <h1>欢迎进入首问责任平台</h1>
            <p>支持用户名或手机号 + 密码登录，进入后可体验问答、名片库、个人中心与运营看板。</p>
          </div>
        </div>
        <el-form class="login-form" :model="form" @submit.prevent>
          <label>
            用户名/手机号
            <el-input v-model="form.account" placeholder="例如：linzhixia / 13800001206" />
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
        <div class="login-tips">
          <span>演示账号：林知夏 / 13800001206</span>
          <span>演示密码：123456</span>
        </div>
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
