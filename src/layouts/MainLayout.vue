<template>
  <div class="app-shell">
    <AppSidebar />
    <main class="main-panel">
      <MainTopbar :display-name="auth.displayName" @command="handleAvatarCommand" />
      <div class="main-content">
        <RouterView />
      </div>
    </main>

    <ChangePasswordDialog v-model="isPasswordDialogOpen" :form="passwordForm" :status="passwordStatus" @submit="changePassword" />
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import AppSidebar from "../components/layout/AppSidebar.vue";
import ChangePasswordDialog from "../components/layout/ChangePasswordDialog.vue";
import MainTopbar from "../components/layout/MainTopbar.vue";
import { useAuthStore } from "../stores/auth.js";

const router = useRouter();
const auth = useAuthStore();
const isPasswordDialogOpen = ref(false);
const passwordStatus = ref("");
const passwordForm = reactive({ currentPassword: "", nextPassword: "", confirmPassword: "" });

async function handleAvatarCommand(command) {
  if (command === "logout") {
    await auth.logout();
    router.push({ name: "login" });
    return;
  }
  if (command === "password") {
    passwordStatus.value = "";
    isPasswordDialogOpen.value = true;
    return;
  }
  router.push({ name: command });
}

function changePassword() {
  const message = auth.changePassword(passwordForm);
  passwordStatus.value = message || "密码已修改";
  if (!message) {
    passwordForm.currentPassword = "";
    passwordForm.nextPassword = "";
    passwordForm.confirmPassword = "";
  }
}
</script>
