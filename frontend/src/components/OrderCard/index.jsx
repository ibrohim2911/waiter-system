import { useNavigate } from "react-router-dom";

const OrderCard = ({order}) => {
	let sortedItems = {};
	// Status color mapping
	const getStatusColor = (order) => {
		// Yellow for processing orders created < 10 min ago
		if (order.order_status === "processing" && order.c_at) {
			const created = new Date(order.c_at);
			const now = new Date();
			const diffMs = now - created;
			if (diffMs < 10 * 60 * 1000) {
				return "border-yellow-400 shadow-yellow-400/50";
			}
			return "border-green-400 shadow-green-400/50";
		}
		switch (order.order_status) {
			case "pending":
				return "border-red-900 shadow-red-800/50";
			case "completed":
				return "border-black";
			default:
				return "border-gray-400 shadow-gray-400/50";
		}
	};

	// Glowing effect color for left bar
	const getGlowColor = order => getStatusColor(order);

	const getMinutesSinceCreated = order => {
		if (order.order_status === "processing" && order.c_at) {
			const created = new Date(order.c_at);
			const now = new Date();
			const minutes = ((now - created) / 1000 / 60).toFixed(2);
			return minutes;
		}
		return null;
	};

	const formatDate = dateString => {
		if (!dateString) return "N/A";
		const date = new Date(dateString);
		return (
			date.toLocaleDateString() +
			" " +
			date.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"})
		);
	};

	order.items.forEach(itm => {
		if (!sortedItems[itm.item_name]) {
			sortedItems[itm.item_name] = {
				total_price: 0,
				quantity: 0,
				item_price: itm.item_price,
			};
		}
		sortedItems[itm.item_name]["quantity"] += parseFloat(itm["quantity"]);
		sortedItems[itm.item_name]["total_price"] += parseFloat(itm["item_price"]) * parseFloat(itm["quantity"]);
	});
	const navigate = useNavigate();
		return (
					<div
						className={`relative bg-zinc-800 rounded-lg shadow-lg p-3 my-2 w-full transition-all duration-300 hover:shadow-xl border-l-4 ${getStatusColor(order)} shadow-lg flex flex-col text-[0.81em] ${order.order_status === 'pending' ? 'text-red-500' : 'text-zinc-100'}`}
						onClick={() => {
							navigate("/order-details", { state: { orderid: order.id } });
						}}
					>
			{/* Glowing effect */}
			<div
				className={`absolute -left-1 top-0 bottom-0 w-1 rounded-l-lg ${getGlowColor(order)} blur-sm opacity-75`}
				title={order.order_status === 'processing' ? `Minutes since created: ${getMinutesSinceCreated(order)}` : undefined}
			></div>

			{/* Header */}
			<div className={`flex justify-between items-center mb-2 pb-2 border-b border-zinc-600 text-[0.81em] ${order.order_status === 'pending' ? 'text-red-500' : ''}`}> 
				<div className="flex flex-col">
					<span className={order.order_status === 'pending' ? 'text-red-500 text-xs' : 'text-xs'}>
						{order.user_name}
					</span>
					<span
						className={`inline-block px-2 py-0.5 text-[1.3em] text-zinc-300 font-medium rounded-full mt-1  ${
							order.order_status === "pending"
								? "bg-yellow-900 text-yellow-200"
								: order.order_status === "in_progress"
								? "bg-blue-900 text-blue-200"
								: order.order_status === "completed"
								? "bg-green-900 text-green-200"
								: "bg-zinc-700 text-zinc-200"
						}`}
					>
						{order.order_status.replace("_", " ").toUpperCase()}
					</span>
				</div>
				<div className="text-right">
					<p className={order.order_status === 'pending' ? 'font-semibold text-base text-red-500 text-[1.5em]' : 'font-semibold text-base text-zinc-100 text-[1.5em]'}>
						{order.table_details?.name || order.table}
					</p>
					{order.table_details?.location && (
						<p className={order.order_status === 'pending' ? 'text-xs text-red-500 text-[1.5em]' : 'text-xs text-zinc-500 text-[1.5em]'}>
							{order.table_details.location}
						</p>
					)}
				</div>
			</div>


			{/* Order Items */}
							<div className="mb-2 h-32 min-h-32 text-[0.81em]">
								<div className="bg-zinc-700 rounded-md p-2 overflow-y-scroll no-scrollbar h-full text-[0.81em]">
					{order.items && order.items.length > 0 ? (
						<ul className="space-y-0.5">
							{Object.keys(sortedItems).map(key => {
								return (
									<li
										key={key}
										className={order.order_status === 'pending' ? 'flex justify-between text-[1.7em] text-red-500' : 'flex justify-between text-[1.7em] text-zinc-200'}
									>
										<span className="flex gap-1 items-center">
											{key} <sub>x{sortedItems[key].quantity}</sub>
										</span>
										<span className="font-medium" >
											{sortedItems[key].total_price} <small>so'm</small>
										</span>
									</li>
								);
							})}
						</ul>
					) : (
						<p className="text-xs text-zinc-400 italic">No items yet</p>
					)}
				</div>
			</div>

			{/* Amount */}
			<div className="mb-0 bg-zinc-700 rounded-md p-1">
				<div className="flex justify-between font-bold text-sm  pt-1 text-[1.3em]">
					<span className={order.order_status === 'pending' ? 'text-red-500' : 'text-zinc-100'}>Total:</span>
					<span className={order.order_status === 'pending' ? 'text-red-500' : 'text-green-400'}>{order.amount}<small> so'm</small></span>
				</div>
			</div>

			{/* Timestamps */}
			
		</div>
	);
};

export default OrderCard;
