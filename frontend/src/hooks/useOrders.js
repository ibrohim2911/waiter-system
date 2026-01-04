import { useState, useCallback } from "react";
import {
  fetchOrders,
  fetchOrder,
  createOrder,
  updateOrder,
  deleteOrder,
} from "../services/orders";

export function useOrders() {
  const [orders, setOrders] = useState([]);
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all orders with pagination and filter
  const getOrders = useCallback(async (params = {}) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchOrders(params);
      setOrders(Array.isArray(res.data) ? res.data : (res.data.results || res.data.orders || []));
      return res.data;
    } catch (err) {
      setError(err.message || "Error fetching orders");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch single order
  const getOrder = useCallback(async (id) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchOrder(id);
      setOrder(res.data);
    } catch (err) {
      setError(err.message || "Error fetching order");
    } finally {
      setLoading(false);
    }
  }, []);

  // Create order
  const addOrder = useCallback(async (orderData) => {
    setLoading(true);
    setError(null);
    try {
      const res = await createOrder(orderData);
      setOrders((prev) => [...prev, res.data]);
      return res.data;
    } catch (err) {
      setError(err.message || "Error creating order");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Update order
  const editOrder = useCallback(async (id, orderData) => {
    setLoading(true);
    setError(null);
    try {
      const res = await updateOrder(id, orderData);
      setOrders((prev) => prev.map((o) => (o.id === id ? res.data : o)));
      return res.data;
    } catch (err) {
      setError(err.message || "Error updating order");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Delete order
  const removeOrder = useCallback(async (id) => {
    setLoading(true);
    setError(null);
    try {
      await deleteOrder(id);
      setOrders((prev) => prev.filter((o) => o.id !== id));
    } catch (err) {
      setError(err.message || "Error deleting order");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {  
    orders,
    order,
    loading,
    error,
    getOrders,
    getOrder,
    addOrder,
    editOrder,
    removeOrder,
  };
}
