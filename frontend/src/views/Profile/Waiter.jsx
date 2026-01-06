import {
  UserCircleIcon,
  ArrowLeftOnRectangleIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  CheckCircleIcon,
  XCircleIcon,
} from "@heroicons/react/24/solid";
import { useAuth } from "../../context/AuthContext";
import { useState, useEffect } from "react";
import { DateRangePicker } from "../../components";
import { getUserStats } from "../../services/statistics";
import { changePassword } from "../../services/auth";
import { format } from "date-fns";

const Waiter = ({ user }) => {
  const { logout } = useAuth();
  const [statsLoading, setStatsLoading] = useState(true);
  const [userStats, setUserStats] = useState(null);
  const [error, setError] = useState("");
  const [statsPeriod, setStatsPeriod] = useState({
    period: "day",
    startDate: new Date(),
    endDate: new Date(),
  });
  const [passwords, setPasswords] = useState({
    old_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setStatsLoading(true);
        const params = {
          period: statsPeriod.period,
        };
        if (statsPeriod.period === 'custom') {
          params.start_time = `${format(statsPeriod.startDate, 'yyyy-MM-dd')}T00:00:00`;
          params.end_time = `${format(statsPeriod.endDate, 'yyyy-MM-dd')}T23:59:59`;
        }
        const stats = await getUserStats(params);
        // Assuming the current user's stats are in this array.
        // The API might return stats for all users, so we find the one for the current user.
        const currentUserStats = stats.user_stats.find(u => u.id === user.id);
        setUserStats(currentUserStats);
      } catch (err) {
        setError('Failed to fetch statistics.');
        console.error(err);
      } finally {
        setStatsLoading(false);
      }
    };

    if (user?.id) {
      fetchStats();
    }
  }, [user, statsPeriod]);

  const handlePasswordInputChange = (e) => {
    const { name, value } = e.target;
    setPasswords((prev) => ({ ...prev, [name]: value }));
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");

    if (passwords.new_password !== passwords.confirm_password) {
      setPasswordError("New passwords don't match.");
      return;
    }

    try {
      await changePassword({
        old_password: passwords.old_password,
        new_password: passwords.new_password,
        confirm_password: passwords.confirm_password,
      });
      setPasswordSuccess("Password changed successfully!");
      setPasswords({
        old_password: "",
        new_password: "",
        confirm_password: "",
      }); // Clear fields on success
    } catch (err) {
      if (err && typeof err === "object" && err.detail) {
        setPasswordError(err.detail);
      } else if (err && typeof err === "object" && err.error) {
        setPasswordError(err.error);
      } else {
        setPasswordError(
          "Failed to change password. Please check the old password."
        );
      }
      console.error(err);
    }
  };

  return (
    <div className="max-h-screen bg-zinc-900 text-zinc-100 p-4 md:p-6 mb-14">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="bg-zinc-800 rounded-lg shadow-xl p-4 mb-4 lg:col-span-1">
          <div className="flex flex-col items-center">
            <UserCircleIcon className="h-16 w-16 text-blue-400 mb-2" />
            <h1 className="text-xl font-bold">{user?.name || user?.username}</h1>
            <p className="text-zinc-400 text-base capitalize">{user?.role}</p>
          </div>
          <div className="mt-4 border-t border-zinc-700 pt-4 space-y-2">
            <div className="flex justify-between">
              <span className="font-semibold text-zinc-400">Phone:</span>
              <span className="text-zinc-200 text-sm">
                {user?.phone_number || "Not provided"}
              </span>
            </div>
          </div>
          <form
            onSubmit={handlePasswordChange}
            className="mt-4 border-t border-zinc-700 pt-4 space-y-3"
          >
            <h3 className="font-semibold text-zinc-300">Reset Password</h3>
            <input
              type="password"
              name="old_password"
              placeholder="Old Password"
              value={passwords.old_password}
              onChange={handlePasswordInputChange}
              className="w-full bg-zinc-700 text-white p-2 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="password"
              name="new_password"
              placeholder="New Password"
              value={passwords.new_password}
              onChange={handlePasswordInputChange}
              className="w-full bg-zinc-700 text-white p-2 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="password"
              name="confirm_password"
              placeholder="Confirm New Password"
              value={passwords.confirm_password}
              onChange={handlePasswordInputChange}
              className="w-full bg-zinc-700 text-white p-2 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {passwordError && (
              <p className="text-red-400 text-xs">{passwordError}</p>
            )}
            {passwordSuccess && (
              <p className="text-green-400 text-xs">{passwordSuccess}</p>
            )}
            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-colors text-sm"
            >
              Update Password
            </button>
          </form>
          <div className="mt-4 border-t border-zinc-700 pt-4">
            <button
              onClick={logout}
              className="w-full flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"
            >
              <ArrowLeftOnRectangleIcon className="h-5 w-5" />
              <span>Logout</span>
            </button>
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="flex flex-wrap items-center justify-between mb-4 gap-4">
            <h2 className="text-2xl font-bold text-zinc-200 flex items-center gap-2">
              <ChartBarIcon className="h-6 w-6" /> Statistics
            </h2>
            <div className="flex flex-wrap items-center gap-4">
              <DateRangePicker onChange={setStatsPeriod} />
            </div>
          </div>

          {statsLoading ? (
            <div className="text-center text-zinc-300">Loading statistics...</div>
          ) : error ? (
            <div className="text-center text-red-400">{error}</div>
          ) : userStats ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-zinc-800 p-4 rounded-lg shadow-lg text-center">
                <CurrencyDollarIcon className="h-8 w-8 mx-auto text-green-400 mb-2" />
                <p className="text-zinc-400 text-sm">Total Earned</p>
                <p className="text-2xl font-bold text-white">
                  ${(userStats.total_earned || 0).toFixed(2)}
                </p>
              </div>
              <div className="bg-zinc-800 p-4 rounded-lg shadow-lg text-center">
                <CurrencyDollarIcon className="h-8 w-8 mx-auto text-yellow-400 mb-2" />
                <p className="text-zinc-400 text-sm">Commission</p>
                <p className="text-2xl font-bold text-white">
                  ${(userStats.earned || 0).toFixed(2)}
                </p>
              </div>
              <div className="bg-zinc-800 p-4 rounded-lg shadow-lg text-center">
                <CheckCircleIcon className="h-8 w-8 mx-auto text-blue-400 mb-2" />
                <p className="text-zinc-400 text-sm">Completed Orders</p>
                <p className="text-2xl font-bold text-white">
                  {userStats.completed_order_count}
                </p>
              </div>
              <div className="bg-zinc-800 p-4 rounded-lg shadow-lg text-center">
                <XCircleIcon className="h-8 w-8 mx-auto text-red-400 mb-2" />
                <p className="text-zinc-400 text-sm">Pending Orders</p>
                <p className="text-2xl font-bold text-white">
                  {userStats.non_completed_order_count}
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center text-zinc-400">No statistics available.</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Waiter;
