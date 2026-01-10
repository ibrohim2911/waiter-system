import api from "./api";

export const getPrinters = async () => {
    const res = await api.get("/printers/");
    return res.data;
}
