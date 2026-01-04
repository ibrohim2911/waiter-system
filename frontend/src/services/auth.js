import api from './api';

export const changePassword = async (passwordData) => {
  try {
    // The passwordData should be an object like { old_password: '...', new_password: '...' }
    const response = await api.put('/change-password/', passwordData);
    return response.data;
  } catch (error) {
    // Re-throw the error so it can be caught and handled in the component
    throw error.response?.data || error;
  }
};