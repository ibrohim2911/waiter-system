function OrderActions({
	order,
	user,
	isEditable,
	onClear,
	onSave,
	onUpdateStatus,
}) {
	return (
		<div className="flex gap-2 p-1 border-t border-zinc-800 bg-zinc-800">
			<button
				className="flex-1 py-1 bg-red-700 text-zinc-100 rounded-lg font-bold text-sm  hover:bg-red-600 transition disabled:opacity-50"
				onClick={onClear}
				disabled={!isEditable}
			>
				Clear
			</button>
			<button
				className="flex-1 py-1 bg-blue-700 text-zinc-100 rounded-lg font-bold text-sm flex items-center justify-center gap-1 hover:bg-blue-600 transition disabled:opacity-50"
				onClick={onSave}
				disabled={!isEditable}
			>
				<span role="img" aria-label="save"></span> Save
			</button>
			{order.order_status === "processing" && (
				<button
					className="flex-1 py-1 bg-yellow-600 text-zinc-100 rounded-lg font-bold text-xs flex items-center justify-center gap-1 hover:bg-yellow-500 transition"
					onClick={() => onUpdateStatus("pending")}
				>
					<span role="img" aria-label="precheque"></span> prechek
				</button>
			)}
			{user && user.role !== "waiter" && (
				<>
					{order.order_status !== "completed" && (
						<button
							className="flex-1 py-3 bg-green-700 text-zinc-100 rounded-lg font-bold text-xs flex items-center justify-center gap-1 hover:bg-green-600 transition"
							onClick={() => onUpdateStatus("completed")}
						>
							<span role="img" aria-label="close"></span> yopish
						</button>
					)}
					{order.order_status !== "processing" && (
						<button
							className="flex-1 py-3 bg-blue-800 text-zinc-100 rounded-lg font-bold text-xs flex items-center justify-center gap-2 hover:bg-blue-700 transition"
							onClick={() => onUpdateStatus("processing")}
						>
							<span role="img" aria-label="open"></span> Ochish
						</button>
					)}
				</>
			)}
		</div>
	);
}

export default OrderActions;
