import api from "./api";

export const getAdminReports = async (period) => {
    const res = await api.get("/reports/admin/", { params: { period } });
    return res.data;
}

export const getInventoryItems = async () => {
    const res = await api.get("/inventory/");
    return res.data;
}

export const getInventoryItem = async (id) => {
    const res = await api.get(`/inventory/${id}/`);
    return res.data;
    /* returns item data:
    {
        id: string,
        name: string,
        quantity: number,
        unit_of_measure: string,
        description: string,
        price: number,
        c_at: string,
        u_at: string,
    }
    */
}


export const createInventoryItem = async (payload) => {
    /*
    payload = {
        name: string, // required
        quantity: number, // default 0
        unit_of_measure: string, // required
        description: string,
        price: number, // required
    }
    */
    const res = await api.post("/inventory/", payload);
    return res.data;
}

export const editInventoryItem = async (itemData) => {
    /*
    itemData = {
        id: string, // required
        name: string, // required
        quantity: number, // required
        unit_of_measure: string, // required
        description: string,
        price: number, // required
    }
    */
    const res = await api.put(`/inventory/${itemData.id}/`, itemData);
    return res.data;
}

export const deleteInventoryItem = async (id) => {
    const res = await api.delete(`/inventory/${id}/`);
    return res.data;
}