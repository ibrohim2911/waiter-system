import api from "./api";

export const places = async () => {
    const response = await api.get("/tables/");
    return response.data.map(table=>table.location)
}

export const tables = async (location) => {
    const response = await api.get("/tables/", {params:{location}});
    return response.data;
}