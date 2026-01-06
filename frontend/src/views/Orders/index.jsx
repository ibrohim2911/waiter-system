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


const LocationFilter = ({ locations, stats, selectedLocation, onSelect, onClear }) => (
	<div className="mb-3">
		<div className="text-zinc-300  font-semibold mb-2">Location</div>
		<div className="space-y-2" >
			{locations.map(location => {
				const pendingStat = stats.pending_order_per_location.find(l => l.table__location === location);
				const processingStat = stats.processing_order_per_location.find(l => l.table__location === location);
				return (
					<div
						key={location}
						className={`cursor-pointer h-10 rounded-lg p-2 transition-all border-2 flex items-center justify-between ${selectedLocation === location ? "bg-blue-600 border-blue-400 text-white" : "bg-zinc-700 border-zinc-600 text-zinc-200 hover:bg-zinc-600"}`}
						onClick={() => onSelect(location)}
					>
						<span>{location}</span>
						<span className="ml-2 text-xs font-bold text-blue-300">{pendingStat?.pending_orders || 0} / {processingStat?.processing_orders || 0}</span>
					</div>
				);
			})}
		</div>
		{selectedLocation && (
			<button className="mt-2 text-blue-300 hover:text-blue-100 text-sm" onClick={onClear}>Clear Location</button>
		)}
	</div>
);


const UserFilter = ({ users, stats, selectedUser, onSelect }) => (
	<div className="mb-3">
		<div className="text-zinc-300 font-semibold mb-2">User</div>
		<div className="space-y-2">
			{users.map(user => {
				const pending = stats.pending_order_per_user.find(u => String(u.id) === String(user.id));
				const processing = stats.processing_order_per_user.find(u => String(u.id) === String(user.id));
				console.log(stats);
				
				return (
					<div
						key={user.id}
						className={`cursor-pointer rounded-lg p-2 transition-all border-2 flex items-center justify-between ${selectedUser === String(user.id) ? "bg-blue-600 border-blue-400 text-white" : "bg-zinc-700 border-zinc-600 text-zinc-200 hover:bg-zinc-600"}`}
						onClick={() => onSelect(String(user.id))}
					>
						<span>{user.username || user.name || user.id}</span>
						<span className="ml-2 text-xs font-bold text-blue-300">{pending?.pending_order_count || 0} / {processing?.processing_order_count || 0}</span>
					</div>
				);
			})}
		</div>
	</div>
);

const Orders = () => {
	const { orders, getOrders, loading } = useOrders();
	const { user } = useAuth();
	const [orderStatuses, setOrderStatuses] = useState(["pending", "processing"]);
	const [locations, setLocations] = useState([]);
	const [selectedLocation, setSelectedLocation] = useState("");
	const [users, setUsers] = useState([]);
	const [selectedUser, setSelectedUser] = useState("");
	const [filterMode, setFilterMode] = useState("location"); // 'location' or 'user'
	const [isWaiter, setIsWaiter] = useState(false);
	const [stats, setStats] = useState(INITIAL_STATS);

	useEffect(()=> {
		const fetchData = async () => {
			const params = {
				"period" : "alltime",
			}
			let data = await fetchOrderStats(params)
			setStats(data.data);
		}
		fetchData()
	}, [])

	useEffect(() => {
		getAllTables().then(tables => {
			const uniqueLocations = [...new Set(tables.map(t => t.location))].filter(Boolean).sort();
			setLocations(uniqueLocations);
		});
	}, []);

	useEffect(() => {
		if (user) {
			if (user.role === "waiter" || user.is_waiter) {
				setIsWaiter(true);
			} else {
				getAllUsers().then(users => setUsers(users));
			}
		}
	}, [user]);

	const viewStats = useMemo(() => {
    if (!stats || !stats.orders_per_user_per_location) return stats;

    // 1. Get data for the specific waiter
    let filteredData = stats.orders_per_user_per_location;
    
    if (isWaiter) {
        filteredData = filteredData.filter(s => s.user__id === user.id);
    }

    // 2. APPLY THE LOCATION FILTER (The part you haven't updated)
    // Assuming your location filter state is called 'activeLocation' or 'selectedLocation'
    if (selectedLocation && selectedLocation !== 'All') {
        filteredData = filteredData.filter(s => s.table__location === selectedLocation);
    }

    // 3. Map to the format the UI expects
    const pending_order_per_location = filteredData.map(entry => ({
        table__location: entry.table__location,
        order_count: entry.pending_orders || 0, 
    }));

    const processing_order_per_location = filteredData.map(entry => ({
        table__location: entry.table__location,
        order_count: entry.processing_orders || 0,
    }));

    return { 
        ...stats, 
        pending_order_per_location, 
        processing_order_per_location 
    };
}, [stats, isWaiter, user, selectedLocation]); // <--- Add selectedLocation here!
	useEffect(() => {
		let params = {
			page_size: 0, // Disable pagination on the backend
		};
		if (orderStatuses.length > 0) {
			params.order_status = orderStatuses.join(",");
		}
		if (selectedLocation) {
			params["table__location"] = selectedLocation;
		}
		if (filterMode === 'user' && selectedUser) {
			params["user"] = selectedUser;
		} else if (isWaiter && user?.id) {
			params["user"] = user.id;
		}
		getOrders(params);
	}, [orderStatuses, selectedLocation, selectedUser, getOrders, filterMode, isWaiter, user]);

		return (
			<div className="min-h-screen h-screen bg-zinc-900 pb-15 flex overflow-hidden text-[0.9em]">
				{/* Sidebar Filters */}
				<div className="w-54 pb-15 bg-zinc-800 border-r-2 border-zinc-700 flex flex-col h-screen max-h-screen shadow-lg z-10 text-[0.9em]">
			<div className="flex-1 min-h-0 overflow-y-auto p-4 scrollbar-custom text-[0.9em]">
					
					{/* Filter mode toggle for non-waiters */}
					{!isWaiter && (
						<>
							<div className="flex gap-2 mb-3">
								<button
									className={`flex-1 h-8 py-1 rounded text-xs font-semibold border ${filterMode === 'location' ? 'bg-blue-600 text-white' : 'bg-zinc-700 text-zinc-200'} transition`}
									onClick={() => {
										setFilterMode('location');
										setSelectedUser(""); // Clear user filter when switching
									}}
								>
									Location Filter
								</button>
								<button
									className={`flex-1 py-1 rounded text-xs font-semibold border ${filterMode === 'user' ? 'bg-blue-600 text-white' : 'bg-zinc-700 text-zinc-200'} transition`}
									onClick={() => {
										setFilterMode('user');
										setSelectedLocation(""); // Clear location filter when switching
									}}
								>
									User Filter
								</button>
							</div>
							{filterMode === 'location' && (
								<LocationFilter
									locations={locations}
									stats={viewStats}
									selectedLocation={selectedLocation}
									onSelect={(location) => setSelectedLocation(selectedLocation === location ? "" : location)}
									onClear={() => setSelectedLocation("")}
								/>
							)}
							{filterMode === 'user' && (
								<UserFilter users={users} stats={viewStats} selectedUser={selectedUser} onSelect={setSelectedUser} />
							)}
						</>
					)}

					{/* Location filter for waiters */}
					{isWaiter && (
						<LocationFilter
							locations={locations}
							stats={viewStats}
							selectedLocation={selectedLocation}
							onSelect={(location) => setSelectedLocation(selectedLocation === location ? "" : location)}
							onClear={() => setSelectedLocation("")}
						/>
					)}
				</div>
			</div>
			{/* Orders List */}
									<div className="flex-1 pb-15 min-w-0 h-screen max-h-screen overflow-y-auto scrollbar-custom text-[0.9em]">
										<div className="p-3 w-full grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 justify-center gap-6 text-[0.9em]">
					{loading ? (
						<div className="col-span-full text-center text-zinc-300">Loading...</div>
					) : orders.length ? (
						[...orders]
							.sort((a, b) => new Date(a.c_at) - new Date(b.c_at))
							.map(order => <OrderCard key={order.id} order={order} />)
					) : (
						<div className="col-span-full text-center text-zinc-400">No orders found.</div>
					)}
				</div>
				
			</div>
		</div>
	);
};

export default Orders;
