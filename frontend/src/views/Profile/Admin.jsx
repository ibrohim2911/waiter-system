import { useState, useEffect } from 'react';
import { me as getMe } from '../../services/getMe';
import { useAuth } from '../../context/AuthContext';
import { changePassword } from '../../services/auth';
import { getAdminReports } from '../../services/inventory';
import { UserCircleIcon, ArrowLeftOnRectangleIcon, ChartBarIcon, CurrencyDollarIcon, ClipboardDocumentListIcon } from '@heroicons/react/24/solid';
import { format } from 'date-fns';
import { DateRangePicker } from '../../components';

const Admin = () => {
  const { logout } = useAuth();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [adminReport, setAdminReport] = useState(null);
  const [error, setError] = useState('');
  const [statsPeriod, setStatsPeriod] = useState({ period: "day", startDate: new Date(), endDate: new Date() });
  const [passwords, setPasswords] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  useEffect(() => {
    const fetchUserAndStats = async () => {
      try {
        setLoading(true);
        const userData = await getMe();
        setUser(userData);

        setStatsLoading(true);
        const params = {
          period: statsPeriod.period,
        };
        if (statsPeriod.period === 'custom') {
          params.start_time = `${format(statsPeriod.startDate, 'yyyy-MM-dd')}T00:00:00`;
          params.end_time = `${format(statsPeriod.endDate, 'yyyy-MM-dd')}T23:59:59`;
        }
        
        const reportData = await getAdminReports(params.period);
        setAdminReport(reportData);

      } catch (err) {
        setError('Failed to fetch data.');
        console.error(err);
      } finally {
        setLoading(false);
        setStatsLoading(false);
      }
    };
    fetchUserAndStats();
  }, [statsPeriod]);

  const handlePasswordInputChange = (e) => {
    const { name, value } = e.target;
    setPasswords(prev => ({ ...prev, [name]: value }));
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    if (passwords.new_password !== passwords.confirm_password) {
      setPasswordError("New passwords don't match.");
      return;
    }

    try {
      await changePassword({ old_password: passwords.old_password, new_password: passwords.new_password, confirm_password: passwords.confirm_password });
      setPasswordSuccess('Password changed successfully!');
      setPasswords({ old_password: '', new_password: '', confirm_password: '' }); // Clear fields on success
    } catch (err) {
      if (err && typeof err === 'object' && err.detail) {
        setPasswordError(err.detail);
      } else if (err && typeof err === 'object' && err.error) {
        setPasswordError(err.error);
      } else {
        setPasswordError('Failed to change password. Please check the old password.');
      }
      console.error(err);
    }
  };

  if (loading || statsLoading) {
    return <div className="text-center text-zinc-300 p-10">Loading profile...</div>;
  }

  if (error || !user) {
    return <div className="text-center text-red-400 p-10">{error || 'User not found.'}</div>;
  }

  return (
    <div className="max-h-screen bg-zinc-900 text-zinc-100 p-4 md:p-6 mb-14" >
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="bg-zinc-800 rounded-lg shadow-xl p-4 mb-4">
          <div className="flex flex-col items-center">
            <UserCircleIcon className="h-16 w-16 text-blue-400 mb-2" />
            <h1 className="text-xl font-bold">{user.name || user.username}</h1>
            <p className="text-zinc-400 text-base capitalize">{user.role}</p>
          </div>
          <div className="mt-4 border-t border-zinc-700 pt-4 space-y-2">
            <div className="flex justify-between">
              <span className="font-semibold text-zinc-400">Phone:</span>
              <span className="text-zinc-200 text-sm">{user.phone_number || 'Not provided'}</span>
            </div>
          </div>
          <form onSubmit={handlePasswordChange} className="mt-4 border-t border-zinc-700 pt-4 space-y-3">
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
            {passwordError && <p className="text-red-400 text-xs">{passwordError}</p>}
            {passwordSuccess && <p className="text-green-400 text-xs">{passwordSuccess}</p>}
            <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-colors text-sm">
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
            <h2 className="text-2xl font-bold text-zinc-200 flex items-center gap-2"><ChartBarIcon className="h-6 w-6" /> Statistics </h2>
            <div className="flex flex-wrap items-center gap-4">
              <DateRangePicker onChange={setStatsPeriod} />
            </div>
          </div>

          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-zinc-800 p-4 rounded-lg shadow-lg text-center">
              <CurrencyDollarIcon className="h-8 w-8 mx-auto text-green-400 mb-2" />
              <p className="text-zinc-400 text-sm">Total Spent</p>
              <p className="text-2xl font-bold text-white">${(adminReport?.total_spent / 100 || 0).toFixed(2)}</p>
            </div>

            <div className="bg-zinc-800 p-4 rounded-lg shadow-lg text-center">
              <CurrencyDollarIcon className="h-8 w-8 mx-auto text-yellow-400 mb-2" />
              <p className="text-zinc-400 text-sm">Total Profit</p>
              <p className="text-2xl font-bold text-white">${(adminReport?.total_profit / 100 || 0).toFixed(2)}</p>
            </div>

            <div className="bg-zinc-800 p-4 rounded-lg shadow-lg text-center">
              <ClipboardDocumentListIcon className="h-8 w-8 mx-auto text-blue-400 mb-2" />
              <p className="text-zinc-400 text-sm">Total Orders</p>
              <p className="text-2xl font-bold text-white">{adminReport?.order_count || 0}</p>
            </div>
          </div>
          
          <div className="bg-zinc-800 p-4 rounded-lg shadow-lg mb-6">
            <h3 className="text-lg font-semibold text-zinc-200 mb-3">User Performance</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left text-zinc-300">
                <thead className="text-xs text-zinc-400 uppercase bg-zinc-700">
                  <tr>
                    <th scope="col" className="px-4 py-2">User</th>
                    <th scope="col" className="px-4 py-2 text-right">Order Count</th>
                    <th scope="col" className="px-4 py-2 text-right">Total Spent</th>
                  </tr>
                </thead>
                <tbody>
                  {adminReport?.waiter_stats?.map(u => (
                    <tr key={u.waiter_id || 'unassigned'} className="border-b border-zinc-700 hover:bg-zinc-700/50">
                      <td className="px-4 py-2 font-medium">{u.name || 'Unassigned'}</td>
                      <td className="px-4 py-2 text-right">{u.order_count}</td>
                      <td className="px-4 py-2 text-right font-semibold">${(u.total_spent / 100).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Admin;