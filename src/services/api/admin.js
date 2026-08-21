import http from "./http.js";

export const fetchAdminMetrics = () => http.get("/admin/metrics");
export const fetchRecommendRanking = () => http.get("/admin/rankings/recommend");
export const fetchActivityTrend = (params) => http.get("/admin/trends/activity", { params });
export const fetchAgentTraces = (params) => http.get("/admin/traces", { params });
export const fetchAgentTraceDetail = (traceId) => http.get(`/admin/traces/${traceId}`);
