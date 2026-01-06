import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token") || null);
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem("refreshToken") || null);
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("user")) || null;
    } catch (e) {
      return null;
    }
  });
  const [loading, setLoading] = useState(true); // Start loading until initial check is done

  useEffect(() => {
    // Since state is initialized synchronously from localStorage,
    // we just need to wait for the first render to pass.
    // This effect runs once after the initial render.
    setLoading(false);
  }, []);

  const login = (data) => {
    const { access, refresh, ...userData } = data;
    setToken(access);
    setRefreshToken(refresh);
    setUser(userData);
    localStorage.setItem("token", access);
    localStorage.setItem("refreshToken", refresh);
    localStorage.setItem("user", JSON.stringify(userData));
  };

  const logout = () => {
    setToken(null);
    setRefreshToken(null);
    setUser(null);
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("user");
  };

  return (
    <AuthContext.Provider value={{ token, refreshToken, user, login, logout, loading, setLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
