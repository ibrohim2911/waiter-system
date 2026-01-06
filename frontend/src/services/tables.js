import api from "./api";

export const getAllTables = async () => {
  const res = await api.get("/tables/");
  return res.data;
};

export const getTable = async (id) => {
  const res = await api.get(`/tables/${id}/`);
  return res.data;
  /* returns table data:
    id: string,
    name: string,
    location: string,
    capacity: number,
    comission: string,
    is_available: boolean
  */
}



export const createTable = async (payload) => {
  /*
  payload = {
    name: string, // required
    location: string, // required
    capacity: number, // required
    comission: string,  // optional
    is_available: boolean, // required
  }
  */
  const res = await api.post(`/tables/`, payload);
  return res.data;
}

export const editTable = async (tableData) => {
  /*
  tableData = {
    name: string, // required
    location: string, // required
    capacity: number, // required
    comission: string,  // optional
    is_active: boolean, // required
  }
  */
  const res = await api.put(`/tables/${tableData.id}/`, tableData);
  return res.data;
}

export const deleteTable = async (id) => {
  const res = await api.delete(`/tables/${id}/`);
  return res.data;
}