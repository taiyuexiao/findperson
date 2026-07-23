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
    isAdmin() {
      return this.user?.systemRole === "管理员";
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
        useDirectoryStore().setCurrentUser(user.id);
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
        useDirectoryStore().setCurrentUser(this.userId);
        this.persist();
        return { ok: true };
      }
      const key = normalize(account);
      const demoAccounts = {
        linzhixia: currentUserId, "林知夏": currentUserId, "13800001206": currentUserId,
        wangke: "p-clerk-1", "王珂": "p-clerk-1", "13800001301": "p-clerk-1",
      };
      const userId = demoAccounts[key];
      if (!userId || password !== this.password) return { ok: false, message: "账号或密码不正确" };
      this.isLoggedIn = true;
      this.userId = userId;
      this.name = useDirectoryStore().getPerson(userId)?.name || "用户";
      useDirectoryStore().setCurrentUser(userId);
      this.persist();
      return { ok: true };
    },
    async logout() {
      if (isServerMode()) await serverLogout().catch(console.warn);
      this.isLoggedIn = false;
      useDirectoryStore().setCurrentUser(currentUserId);
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
      const person = useDirectoryStore().updatePerson(this.userId, {
        contact: patch.contact,
        domainsText: patch.domainsText,
        selfPortrait: patch.selfPortrait,
      });
      if (person) {
        this.name = person.name;
        this.persist();
        if (isServerMode()) updateMyProfile(person).catch(console.warn);
      }
      return person;
    },
  },
});
