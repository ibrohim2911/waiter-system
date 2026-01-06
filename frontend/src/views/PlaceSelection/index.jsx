import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import usePlaceSelection from "../../hooks/usePlaceSelection";
import { LocationCard, TableCard } from "../../components";
import { useOrders } from "../../hooks/useOrders";
import { me as getMe } from "../../services/getMe";

const PlaceSelection = () => {
	const navigate = useNavigate();
	const location = useLocation();
	const { addOrder } = useOrders();
	const {
		locations,
		selectedLocation,
		availableTables,
		selectLocation,
		selectTable,
		isLoading,
		error,
		isLoadingLocations,
		isLoadingTables,
		getTableCountForLocation,
	} = usePlaceSelection();

	const handleTableSelect = async table => {
		
		let me = await getMe();
		if (!me) {
			navigate("/login");
			return;
		}
		const orderid = location.state?.orderid;
		if (orderid) {
			const { updateOrder } = await import("../../services/orders");
			await updateOrder(orderid, { table: table.id });
			selectTable(table);
			navigate("/order-details", {
				state: {
					selectedLocation,
					selectedTable: table,
					orderid: orderid,
				},
			});
		} else {
			const order = await addOrder({
				table: table.id,
				user: me.id,
				order_status: "processing",
			});
			selectTable(table);
			navigate("/order-details", {
				state: {
					selectedLocation,
					selectedTable: table,
					orderid: order.id,
				},
			});
		}
	};

	if (isLoadingLocations) {
		return (
			<div className="flex justify-center items-center min-h-screen bg-zinc-900">
				<div className="text-zinc-100">Joylar yuklanmoqda...</div>
			</div>
		);
	}

	return (
		<div className="h-screen bg-zinc-900 flex overflow-hidden pb-15">
			{error && (
				<div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-red-900 text-red-200 p-3 rounded-lg z-10">
					{error}
				</div>
			)}
			{/* Left Sidebar - Locations */}
			<div className="w-80 bg-zinc-800 border-r border-zinc-700 flex flex-col h-full">
				{/* Sidebar Header */}
				<div className="p-4 border-b border-zinc-700 flex-shrink-0">
					<h2 className="text-zinc-100 text-lg font-bold">Joyni tanlang</h2>
					{selectedLocation && (
						<div className="mt-2 flex items-center bg-blue-900 rounded-lg px-3 py-1">
							<span className="text-blue-200 text-sm font-medium">{selectedLocation}</span>
							<button onClick={() => selectLocation("")} className="ml-2 text-blue-300 hover:text-blue-100 text-lg">✕</button>
						</div>
					)}
				</div>
				{/* Locations List */}
				<div className="flex-1 overflow-y-auto no-scrollbar p-4">
					{isLoadingLocations ? (
						<div className="flex justify-center py-8">
							<div className="text-zinc-400">Joylar yuklanmoqda...</div>
						</div>
					) : (
						<div className="space-y-3">
							{locations.map(location => (
								<LocationCard
									key={location}
									location={location}
									isSelected={selectedLocation === location}
									onSelect={selectLocation}
									getTableCount={getTableCountForLocation}
								/>
							))}
						</div>
					)}
				</div>
			</div>
			{/* Right Content - Tables */}
			<div className="flex-1 flex flex-col h-full">
				{/* Tables Header */}
				<div className="p-4 border-b border-zinc-700 bg-zinc-800 flex-shrink-0">
					<h3 className="text-zinc-100 text-lg font-semibold">
						{selectedLocation ? `${selectedLocation} - Stollarni tanlang` : "Stollar"}
					</h3>
				</div>
				{/* Tables Grid or Message */}
				<div className="flex-1 overflow-y-auto no-scrollbar p-4">
					{!selectedLocation ? (
						<div className="flex items-center justify-center h-full">
							<div className="text-center">
								<div className="text-zinc-400 text-xl mb-2">Avval joyni tanlang</div>
								<div className="text-zinc-500 text-sm">Stollarni ko'rish uchun chap tarafdan joyni bosing</div>
							</div>
						</div>
					) : isLoadingTables ? (
						<div className="flex items-center justify-center h-full">
							<div className="text-zinc-400 text-lg">Stollar yuklanmoqda...</div>
						</div>
					) : availableTables.length > 0 ? (
						<div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
							{availableTables.map(table => (
								<TableCard key={table.id} table={table} onSelect={handleTableSelect} />
							))}
						</div>
					) : (
						<div className="flex items-center justify-center h-full">
							<div className="text-center">
								<div className="text-zinc-400 text-lg mb-2">Bu joyda stollar topilmadi</div>
								<div className="text-zinc-500 text-sm">Boshqa joy tanlang</div>
							</div>
						</div>
					)}
				</div>
			</div>
		</div>
	);
};

export default PlaceSelection;
