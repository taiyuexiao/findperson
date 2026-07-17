import { defineStore } from "pinia";
import { currentUserId, loadJson, normalize, saveJson, STORAGE_KEYS } from "../state.js";
import { getMe, login as serverLogin, logout as serverLogout, updateMyProfile } from "../services/api/auth.js";
import { isServerMode } from "../services/mode.js";
import { useDirectoryStore } from "./directory.js";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    ...loadJson(STORAGE_KEYS.auth, {
      isLoggedIn: true,
      userId: currentUserId,
      name: "林知夏",
      password: "123456",
    }),
  }),
  getters: {
    user() {
      return useDirectoryStore().getPerson(this.userId);
    },
    displayName() {
      return this.user?.name || this.name || "用户";
    },
  },
  actions: {
    persist() {
      saveJson(STORAGE_KEYS.auth, {
        isLoggedIn: this.isLoggedIn,
        userId: this.userId,
        name: this.displayName,
        password: this.password,
      });
    },
    async loadMe() {
      if (!isServerMode()) return this.user;
      const user = await getMe();
      if (user?.id) {
        this.userId = user.id;
        this.name = user.name;
        this.isLoggedIn = true;
        this.persist();
      }
      return user;
    },
    async login({ account, password }) {
      if (isServerMode()) {
        const result = await serverLogin({ account, password });
        if (result?.token) localStorage.setItem("firstResponsibilityDemo.token", result.token);
        this.isLoggedIn = true;
        this.userId = result?.user?.id || currentUserId;
        this.name = result?.user?.name || this.displayName;
        this.persist();
        return { ok: true };
      }
      const key = normalize(account);
      const ok = ["linzhixia", "林知夏", "13800001206"].includes(key) && password === this.password;
      if (!ok) return { ok: false, message: "账号或密码不正确" };
      this.isLoggedIn = true;
      this.userId = currentUserId;
      this.name = this.displayName;
      this.persist();
      return { ok: true };
    },
    async logout() {
      if (isServerMode()) await serverLogout().catch(console.warn);
      this.isLoggedIn = false;
      localStorage.removeItem("firstResponsibilityDemo.token");
      this.persist();
    },
    changePassword({ currentPassword, nextPassword, confirmPassword }) {
      if (currentPassword !== this.password) return "原密码不正确";
      if (!nextPassword || nextPassword.length < 6) return "新密码至少 6 位";
      if (nextPassword !== confirmPassword) return "两次输入不一致";
      this.password = nextPassword;
      this.persist();
      return "";
    },
    updateProfile(patch) {
      const person = useDirectoryStore().updatePerson(this.userId, patch);
      if (person) {
        this.name = person.name;
        this.persist();
        if (isServerMode()) updateMyProfile(person).catch(console.warn);
      }
      return person;
    },
  },
});
