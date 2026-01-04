function OrderTotals({subtotal, commission, total}) {
	return (
		<div className="border-t border-zinc-800 px-2 py-1 bg-zinc-800">
			<div className="flex justify-between text-xs text-zinc-300">
				<span>Subtotal:</span>
				<span>
					{subtotal} so'm + {commission}%
				</span>
			</div>
			<div className="text-right text-xl font-bold mt-1 text-blue-300">
				{total} <small>so'm</small>
			</div>
		</div>
	);
}

export default OrderTotals;
