import {TableCellsIcon} from "@heroicons/react/24/outline";

function OrderHeader({order, isEditable, onNavigate}) {
	return (
		<>
			<div className="flex items-center justify-between bg-zinc-800 px-2 py-1 border-b border-zinc-700">
				<div>
					<span className="font-bold text-sm text-zinc-100">ORDER</span>
					<span className="text-zinc-400 ml-1">#{order.id}</span>
				</div>
				<div>
					<span className="font-bold text-blue-300">{order.user_name}</span>
				</div>
			</div>
			<div className="flex items-center justify-between px-2 py-2 border-b border-zinc-800 text-zinc-200 bg-zinc-800">
				<span className="flex items-center  text-[0.7em]">
					<span role="img" aria-label="calendar ">
						📅
					</span>{" "}
					{order.c_at ? new Date(order.c_at).toLocaleString() : "-"}
				</span>
				<span className="text-[0.8em]">
					<TableCellsIcon className="w-4 h-4 inline-block" />
					<span
						className="ml-1 px-1 py-1 cursor-pointer select-none text-blue-400 underline"
						onClick={() => {
							if (!isEditable) return;
							onNavigate("/create-order", {state: {orderid: order.id}});
						}}
					>
						{order.table_details?.name}
					</span>
					<span className="ml-1 px-1 py-1 select-none">
						{order.table_details?.location}
					</span>
				</span>
			</div>
		</>
	);
}

export default OrderHeader;
