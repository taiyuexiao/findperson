import http from "./http.js";

export const fetchSessions = () => http.get("/sessions");
export const createSession = (payload) => http.post("/sessions", payload);
export const updateSession = (id, payload) => http.patch(`/sessions/${id}`, payload);
export const deleteSession = (id) => http.delete(`/sessions/${id}`);
export const fetchSessionMessages = (id) => http.get(`/sessions/${id}/messages`);
