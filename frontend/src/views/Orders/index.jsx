import React, { useState, useEffect, useMemo } from "react";
import { useOrders } from "../../hooks/useOrders";
import OrderCard from "../../components/OrderCard";
import { getAllTables } from "../../services/tables";
import { getAllUsers } from "../../services/users";
import { useAuth } from "../../context/AuthContext";
import { fetchOrderStats } from "../../services/orderStats";

const INITIAL_STATS = {
    orders_per_user_per_location: [],
    orders_per_user: [],
    pending_order_per_user: [],
    processing_order_per_user: [],
    orders_per_table_location: [],
    pending_order_per_location: [],
    processing_order_per_location: [],
};

// --- LOCATION FILTER COMPONENT ---
const LocationFilter = ({ locations, stats, selectedLocation, onSelect, onClear }) => (
    <div className="mb-3">
        <div className="text-zinc-300 font-semibold mb-2">joylashuv</div>
        <div className="space-y-2">
            {locations.map(location => {
                // DEBUG: Check if we can find the location in the mapped stats
                const pendingStat = stats.pending_order_per_location?.find(l => l.table__location === location);
                const processingStat = stats.processing_order_per_location?.find(l => l.table__location === location);
                
                return (
                    <div
                        key={location}
                        className={`cursor-pointer h-10 rounded-lg p-2 transition-all border-2 flex items-center justify-between ${selectedLocation === location ? "bg-blue-600 border-blue-400 text-white" : "bg-zinc-700 border-zinc-600 text-zinc-200 hover:bg-zinc-600"}`}
                        onClick={() => onSelect(location)}
                    >
                        <span>{location}</span>
                        <span className="ml-2 text-xs font-bold text-blue-300">
                            {/* Ensure we read the keys exactly as mapped in viewStats */}
                            {pendingStat?.pending_orders || 0} / {processingStat?.processing_orders || 0}
                        </span>
                    </div>
                );
            })}
        </div>
        {selectedLocation && (
            <button className="mt-2 text-blue-300 hover:text-blue-100 text-sm" onClick={onClear}>filterni tozalash</button>
        )}
    </div>
);

// --- USER FILTER COMPONENT ---
const UserFilter = ({ users, stats, selectedUser, onSelect }) => (
    <div className="mb-3">
        <div className="text-zinc-300 font-semibold mb-2">Foydalanuvchi</div>
        <div className="space-y-2">
            {users.map(user => {
                const pending = stats.pending_order_per_user?.find(u => String(u.id) === String(user.id));
                const processing = stats.processing_order_per_user?.find(u => String(u.id) === String(user.id));
                
                return (
                    <div
                        key={user.id}
                        className={`cursor-pointer rounded-lg p-2 transition-all border-2 flex items-center justify-between ${selectedUser === String(user.id) ? "bg-blue-600 border-blue-400 text-white" : "bg-zinc-700 border-zinc-600 text-zinc-200 hover:bg-zinc-600"}`}
                        onClick={() => onSelect(String(user.id))}
                    >
                        <span>{user.username || user.name || user.id}</span>
                        <span className="ml-2 text-xs font-bold text-blue-300">
                            {pending?.pending_order_count || 0} / {processing?.processing_order_count || 0}
                        </span>
                    </div>
                );
            })}
        </div>
    </div>
);

// --- MAIN COMPONENT ---
const Orders = () => {
    const { orders, getOrders, loading } = useOrders();
    const { user } = useAuth();
    const [orderStatuses, setOrderStatuses] = useState(["pending", "processing"]);
    const [locations, setLocations] = useState([]);
    const [selectedLocation, setSelectedLocation] = useState("");
    const [users, setUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState("");
    const [filterMode, setFilterMode] = useState("location");
    const [isWaiter, setIsWaiter] = useState(false);
    const [stats, setStats] = useState(INITIAL_STATS);

    // 1. Fetch Stats
    useEffect(() => {
        const fetchData = async () => {
            const params = { "period": "alltime" };
            let data = await fetchOrderStats(params);
            
            setStats(data.data);
        };
        fetchData();
    }, []);

    // 2. Fetch Locations
    useEffect(() => {
        getAllTables().then(tables => {
            const uniqueLocations = [...new Set(tables.map(t => t.location))].filter(Boolean).sort();
            setLocations(uniqueLocations);
        });
    }, []);

    // 3. Set Role
    useEffect(() => {
        if (user) {
            
            if (user.role === "waiter" || user.is_waiter) {
                setIsWaiter(true);
            } else {
                getAllUsers().then(users => setUsers(users));
            }
        }
    }, [user]);

    // 4. CALCULATE STATS (THE IMPORTANT PART)
    const viewStats = useMemo(() => {
        // Safety check
        if (!stats || !stats.orders_per_user_per_location) return INITIAL_STATS;

        // Debugging Logsconst viewStats = useMemo(() => {
    // 1. If stats hasn't loaded yet, return the initial empty state
    if (!stats || !stats.orders_per_user_per_location) return INITIAL_STATS;

    // 2. If it's an Admin, we use the global stats as they are
    if (!isWaiter) return stats;

    // 3. IF WAITER: The backend already filtered for us!
    // We just need to "re-map" the data so the LocationFilter can find it.
    

    const pendingMapped = stats.orders_per_user_per_location.map(item => ({
        table__location: item.table__location,
        pending_orders: item.pending_orders || 0 
    }));

    const processingMapped = stats.orders_per_user_per_location.map(item => ({
        table__location: item.table__location,
        processing_orders: item.processing_orders || 0 
    }));

    return {
        ...stats,
        // We tell the UI: "Here is the list of locations specifically for you"
        pending_order_per_location: pendingMapped,
        processing_order_per_location: processingMapped
    };
}, [stats, isWaiter]); // Removed 'user' because we trust the backend token

    // 5. Fetch Orders List
    useEffect(() => {
        let params = { page_size: 0 };
        if (orderStatuses.length > 0) params.order_status = orderStatuses.join(",");
        if (selectedLocation) params["table__location"] = selectedLocation;
        
        if (filterMode === 'user' && selectedUser) {
            params["user"] = selectedUser;
        } else if (isWaiter && user?.id) {
            params["user"] = user.id;
        }
        getOrders(params);
    }, [orderStatuses, selectedLocation, selectedUser, getOrders, filterMode, isWaiter, user]);

    return (
        <div className="min-h-screen h-screen bg-zinc-900 pb-15 flex overflow-hidden text-[0.9em]">
            <div className="w-54 pb-15 bg-zinc-800 border-r-2 border-zinc-700 flex flex-col h-screen max-h-screen shadow-lg z-10 text-[0.9em]">
                <div className="flex-1 min-h-0 overflow-y-auto p-4 scrollbar-custom">
                    {!isWaiter ? (
                        <>
                            <div className="flex gap-2 mb-3">
                                <button
                                    className={`flex-1 h-8 py-1 rounded text-xs font-semibold border ${filterMode === 'location' ? 'bg-blue-600 text-white' : 'bg-zinc-700 text-zinc-200'} transition`}
                                    onClick={() => { setFilterMode('location'); setSelectedUser(""); }}
                                >
                                    joylashuv
                                </button>
                                <button
                                    className={`flex-1 py-1 rounded text-xs font-semibold border ${filterMode === 'user' ? 'bg-blue-600 text-white' : 'bg-zinc-700 text-zinc-200'} transition`}
                                    onClick={() => { setFilterMode('user'); setSelectedLocation(""); }}
                                >
                                    Foydalanuvchi
                                </button>
                            </div>
                            {filterMode === 'location' && (
                                <LocationFilter
                                    locations={locations}
                                    stats={viewStats}
                                    selectedLocation={selectedLocation}
                                    onSelect={(loc) => setSelectedLocation(selectedLocation === loc ? "" : loc)}
                                    onClear={() => setSelectedLocation("")}
                                />
                            )}
                            {filterMode === 'user' && (
                                <UserFilter users={users} stats={viewStats} selectedUser={selectedUser} onSelect={setSelectedUser} />
                            )}
                        </>
                    ) : (
                        <LocationFilter
                            locations={locations}
                            stats={viewStats}
                            selectedLocation={selectedLocation}
                            onSelect={(loc) => setSelectedLocation(selectedLocation === loc ? "" : loc)}
                            onClear={() => setSelectedLocation("")}
                        />
                    )}
                </div>
            </div>

            <div className="flex-1 pb-15 min-w-0 h-screen max-h-screen overflow-y-auto scrollbar-custom">
                <div className="p-3 w-full grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 justify-center gap-6">
                    {loading ? (
                        <div className="col-span-full text-center text-zinc-300">yuklanmoqda...</div>
                    ) : orders.length ? (
                        [...orders]
                            .sort((a, b) => new Date(a.c_at) - new Date(b.c_at))
                            .map(order => <OrderCard key={order.id} order={order} />)
                    ) : (
                        <div className="col-span-full text-center text-zinc-400">buyurtmalar topilmadi.</div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Orders;