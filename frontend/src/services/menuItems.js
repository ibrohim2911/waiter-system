import api from "./api";

export const getMenuItems = async () => {
    const res = await api.get("/menuitems/");
    return res.data;
}

export const getMenuItem = async (id) => {

    // returns item data:
    /*
    {
        id: string,
        name: string,
        description: string,
        price: number,
        category: string,
        is_available: boolean,
        is_frequent: boolean,
        c_at: string,
        u_at: string,
    }
    */
    const res = await api.get(`/menuitems/${id}/`);
    return res.data;
}

export const createMenuItem = async (payload) => {
    /*
    payload = {
        name: string, // required
        description: string,
        price: number, // required
        category: string, // required
        is_frequent: boolean, // default false
    }
    */
    const res = await api.post("/menuitems/", payload);
    return res.data;
}

export const editMenuItem = async (itemData) => {
    /*
    itemData = {
        id: string, // required
        name: string, // required
        description: string,
        price: number, // required
        category: string, // required
        is_frequent: boolean, // required
    }
    */
    const res = await api.put(`/menuitems/${itemData.id}/`, itemData);
    return res.data;
}

export const deleteMenuItem = async (id) => {
    const res = await api.delete(`/menuitems/${id}/`);
    return res.data;
}