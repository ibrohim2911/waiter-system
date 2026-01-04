import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ProtectedRoute = ({ allowedRoles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="text-zinc-300 p-10 text-center">Loading...</div>;
  }

  if (!user) {
    // If user is not loaded yet but token exists (handled by App.jsx), 
    // we might want to wait or redirect. 
    // Since App.jsx handles the login screen, if we are here, we expect a user.
    // But if fetchUser failed or is in progress, we handle loading above.
    return <Navigate to="/" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
