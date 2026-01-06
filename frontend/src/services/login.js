import { useCallback } from 'react';
import api from './api';
import { useAuth } from '../context/AuthContext';

// Login with phone and password
export const login = async ({ phone, password }) => {
  const response = await api.post('/phone-jwt-login/', { phone_number: phone, password });
  // Save tokens to localStorage
  return response.data;
};

// Login with phone and pin
export const pinLogin = async ({ pin }) => {
  const response = await api.post('/pin-login/', { pin: parseInt(pin) });
  return response.data;
};

// React hook for login
export function useLogin() {
  const { login: contextLogin } = useAuth();
  return useCallback(async (phone, password) => {
    const data = await login({ phone, password });
    contextLogin(data);
    return data;
  }, [contextLogin]);
}

// React hook for pin login
export function usePinLogin() {
  const { login: contextLogin } = useAuth();
  return useCallback(async (pin) => {
    const data = await pinLogin({ pin });
    contextLogin(data);
    return data;
  }, [contextLogin]);
}
