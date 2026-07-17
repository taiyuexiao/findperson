import { createRouter, createWebHistory } from "vue-router";
import MainLayout from "../layouts/MainLayout.vue";
import LoginView from "../views/LoginView.vue";
import AskView from "../views/AskView.vue";
import DirectoryView from "../views/DirectoryView.vue";
import MineView from "../views/MineView.vue";
import ManualView from "../views/ManualView.vue";
import ProfileView from "../views/ProfileView.vue";
import ReviewView from "../views/ReviewView.vue";
import PublishView from "../views/PublishView.vue";
import ContentDetailView from "../views/ContentDetailView.vue";
import AdminView from "../views/AdminView.vue";
import { useAuthStore } from "../stores/auth.js";
import { useContentStore } from "../stores/content.js";
import { useDirectoryStore } from "../stores/directory.js";
import { useReviewsStore } from "../stores/reviews.js";
import { useSessionsStore } from "../stores/sessions.js";

const routes = [
  { path: "/", redirect: "/ask" },
  { path: "/login", name: "login", component: LoginView },
  {
    path: "/",
    component: MainLayout,
    children: [
      { path: "ask", name: "ask", component: AskView },
      { path: "directory", name: "directory", component: DirectoryView },
      { path: "mine", name: "mine", component: MineView },
      { path: "manual", name: "manual", component: ManualView },
      { path: "profile/:id", name: "profile", component: ProfileView },
      { path: "review", name: "review", component: ReviewView },
      { path: "publish", name: "publish", component: PublishView },
      { path: "content/:id", name: "contentDetail", component: ContentDetailView },
      { path: "admin", name: "admin", component: AdminView },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  const sessions = useSessionsStore();
  sessions.init();
  await Promise.all([
    useDirectoryStore().loadPeople(),
    useContentStore().loadContents(),
    useReviewsStore().loadReviews(),
    sessions.loadSessions(),
  ]);
  document.body.classList.toggle("is-login-view", to.name === "login");
  if (to.name !== "login" && !auth.isLoggedIn) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if (to.name === "login" && auth.isLoggedIn) return { name: "ask" };
  return true;
});

export default router;
