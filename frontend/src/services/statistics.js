import api from "./api";

export const getOrderStats = async (params) => {
  const res = await api.get("/order-stats/", { params });
  return res.data;
};

export const getUserStats = async (params) => {
  const res = await api.get("/user-stats/", { params });
  return res.data;
};
