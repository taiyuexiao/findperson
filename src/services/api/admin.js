import http from "./http.js";

export const fetchAdminMetrics = () => http.get("/admin/metrics");
export const fetchRecommendRanking = () => http.get("/admin/rankings/recommend");
export const fetchActivityTrend = (params) => http.get("/admin/trends/activity", { params });
export const fetchFeedbackSummary = () => http.get("/admin/feedback/summary");
export const fetchFeedbackRecent = (params) => http.get("/admin/feedback/recent", { params });
