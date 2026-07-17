import http from "./http.js";

export const fetchPeople = (params) => http.get("/people", { params });
export const fetchPerson = (id) => http.get(`/people/${id}`);
export const fetchDepartmentTree = () => http.get("/departments/tree");
