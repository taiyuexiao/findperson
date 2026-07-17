import http from "./http.js";

export const createReview = (payload) => http.post("/reviews", payload);
export const fetchSentReviews = () => http.get("/reviews/sent");
export const fetchPersonReviews = (personId) => http.get(`/people/${personId}/reviews`);
export const deleteReview = (id) => http.delete(`/reviews/${id}`);
