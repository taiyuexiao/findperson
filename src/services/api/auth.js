import http from "./http.js";

export const login = (payload) => http.post("/auth/login", payload);
export const logout = () => http.post("/auth/logout");
export const getMe = () => http.get("/me");
export const updateMyProfile = (payload) => http.put("/me/profile", payload);
