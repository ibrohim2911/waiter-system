import { useState, useEffect, use } from 'react';
import { getAdminReports } from '../../services/inventory';
import { DateRangePicker } from '../../components';
import { useNavigate } from 'react-router';

const Inventory = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState('month');
  const navigate = useNavigate();

  const handleDateRangeChange = ({ period: newPeriod, startDate: start, endDate: end }) => {
    // todo: do some stuff
  }

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await getAdminReports(period);
        setStats(res);
      } catch (err) {
        console.error('Failed to fetch stats:', err);
        setError('Failed to load statistics');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [period]);

  if (loading) {
    return (
      <div className="w-full min-h-screen bg-zinc-900 text-white flex items-center justify-center">
        <div className="text-lg text-zinc-400">Loading statistics...</div>
      </div>
    );
  }

  if (!stats) return null;

  const summary = stats.reports?.consolidated_summary || {};

  return (
    <div className="w-full min-h-screen bg-zinc-900 text-white p-6 mb-10">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex justify-between items-center flex-wrap">
          <div>
            <h1 className="text-4xl font-bold mb-2">Statistics</h1>
            <p className="text-zinc-400 text-sm">
              {new Date(stats.start).toLocaleDateString()} - {new Date(stats.end).toLocaleDateString()}
            </p>
          </div>
          <div onClick={()=>navigate("/inventory/crud")} className="bg-zinc-800 border-2 selection:bg-transparent border-blue-600 p-2 rounded-lg flex items-center cursor-pointer">CRUD</div>
          <DateRangePicker onChange={handleDateRangeChange} />
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-900 text-red-200 rounded-lg">{error}</div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <MetricCard label="Gross Sales" value={`${stats.total_spent || 0}`} />
          <MetricCard label="Commission" value={`${stats.total_profit || 0}`} />
          <MetricCard label="Pure Profit" value={`${stats.total_pure_profit || 0}`} />
          <MetricCard label="Orders" value={stats.order_count || 0} />
        </div>

        {/* Summary Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Revenue by Category */}
          {stats.reports?.revenue_by_category && stats.reports.revenue_by_category.length > 0 && (
            <Card title="Revenue by Category">
              <div className="space-y-3">
                {stats.reports.revenue_by_category.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-zinc-400 capitalize">{item.category}</span>
                    <span className="text-lg font-semibold">{item.total_revenue}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Top Dishes by Revenue */}
          {stats.reports?.dish_sales && stats.reports.dish_sales.length > 0 && (
            <Card title="Top Dishes by Revenue">
              <div className="space-y-3">
                {stats.reports.dish_sales.slice(0, 5).map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-zinc-400">{item.name}</span>
                    <span className="text-lg font-semibold">{item.total_revenue}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Waiter Stats */}
        {stats.waiter_stats && stats.waiter_stats.length > 0 && (
          <Card title="Waiter Performance">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-700">
                    <th className="text-left py-3 text-zinc-400">Name</th>
                    <th className="text-left py-3 text-zinc-400">Orders</th>
                    <th className="text-right py-3 text-zinc-400">Total Sales</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.waiter_stats.map((waiter, idx) => (
                    <tr key={idx} className="border-b border-zinc-800">
                      <td className="py-3">{waiter.name}</td>
                      <td className="py-3">{waiter.order_count}</td>
                      <td className="text-right py-3">{waiter.total_spent}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Dish Consumption */}
        {stats.reports?.dish_consumption && stats.reports.dish_consumption.length > 0 && (
          <Card title="Dish Consumption">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-700">
                    <th className="text-left py-3 text-zinc-400">Dish</th>
                    <th className="text-left py-3 text-zinc-400">Category</th>
                    <th className="text-right py-3 text-zinc-400">Quantity</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.reports.dish_consumption.map((item, idx) => (
                    <tr key={idx} className="border-b border-zinc-800">
                      <td className="py-3">{item.name}</td>
                      <td className="py-3 capitalize text-zinc-400">{item.category}</td>
                      <td className="text-right py-3 font-semibold">{item.total_quantity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Inventory Stats */}
        {stats.inventory_stats && stats.inventory_stats.length > 0 && (
          <Card title="Inventory Status">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {stats.inventory_stats.map((item, idx) => (
                <div key={idx} className="p-4 bg-zinc-700 rounded-lg">
                  <h4 className="font-semibold mb-2">{item.name}</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-zinc-400">Used:</span>
                      <span>{item.used_quantity}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-400">Remaining:</span>
                      <span className="font-semibold">{item.remaining_quantity}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Open Orders by Hall */}
        {stats.reports?.open_orders_by_hall && stats.reports.open_orders_by_hall.length > 0 && (
          <Card title="Open Orders by Hall">
            <div className="space-y-3">
              {stats.reports.open_orders_by_hall.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center p-3 bg-zinc-700 rounded-lg">
                  <div>
                    <p className="font-semibold capitalize">{item.hall}</p>
                    <p className="text-sm text-zinc-400">{item.open_orders_count} open orders</p>
                  </div>
                  <span className="text-lg font-semibold">{item.open_orders_subtotal}</span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

const MetricCard = ({ label, value }) => (
  <div className="p-4 bg-zinc-800 rounded-lg border border-zinc-700">
    <p className="text-zinc-400 text-sm font-medium mb-2">{label}</p>
    <p className="text-2xl font-bold">{value}</p>
  </div>
);

const Card = ({ title, children }) => (
  <div className="p-6 bg-zinc-800 rounded-lg border border-zinc-700 mb-6">
    <h3 className="text-lg font-semibold mb-4">{title}</h3>
    {children}
  </div>
);

export default Inventory