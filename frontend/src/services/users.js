import api from "./api";

export const getAllUsers = async () => {
  const res = await api.get("/users/");
  return res.data;
};

export const createUser = async (payload) => {
  const res = await api.post("/users/", payload);
  return res.data;
};

export const EditUser = async (userData) => {
  /*
  userData = {
    id: string, // required
    name: string, // required
    role: string, // required
    phone_number: string,
    email: string,
  */

  const res = await api.post("/users/put/", userData);
  return res.data;
}

export const deleteUser = async (id) => {
  // Try conventional REST delete first
  try {
    const res = await api.delete(`/users/${id}/`);
    return res.data;
  } catch (err) {
    // Fallback to legacy endpoint if needed
    const res = await api.post(`/users/delete/`, { id });
    return res.data;
  }
};