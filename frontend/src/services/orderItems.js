import api from './api';

// Create a new order item
export const createOrderItem = async (order, menu_item, quantity) => {
  const res = await api.post('/orderitems/', { order, menu_item, quantity });
  return res;
};

// Create a new order item list
export const createOrderItemList = async (itemList) => {
  const res = await api.post('/orderitems/', itemList);
  return res;
};

// Update an order item (by id)
export const updateOrderItem = async (id, data) => {
  const res = await api.put(`/orderitems/${id}/`, data);
  return res;
};

// Delete an order item (by id)
export const deleteOrderItem = (id) =>
  api.delete(`/orderitems/${id}/`);
