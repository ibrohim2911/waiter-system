import api from "./api";


export const fetchOrderStats = (params = {}) => api.get(`/order-stats/`, { params });