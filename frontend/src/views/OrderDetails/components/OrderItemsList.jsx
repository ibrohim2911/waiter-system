import React from "react";
import Numpad from "../../../components/Numpad";
import { DocumentDuplicateIcon, XMarkIcon } from '@heroicons/react/24/solid';

// Helper to show time since last update
function timeSince(date) {
	if (!date) return "-";
	const now = new Date();
	const updated = new Date(date);
	const seconds = Math.floor((now - updated) / 1000);
	if (seconds < 60) return `${seconds} sekund `;
	const minutes = Math.floor(seconds / 60);
	if (minutes < 60) return `${minutes} minut `;
	const hours = Math.floor(minutes / 60);
	if (hours < 24) return `${hours} soat`;
	const days = Math.floor(hours / 24);
	return `${days} kun${days > 1 ? "lar" : ""}`;
}

function OrderItemsList({
	savedItems,
	newItems,
	selectedItemKey,
	onItemSelect,
}) {
	if (savedItems.length === 0 && newItems.length === 0) {
		return (
			<div className="text-zinc-500 text-center py-4">
				No items in order.
			</div>
		);
	}

	return (
		<div className="flex-1 overflow-y-auto px-2 py-2">
			{savedItems.length > 0 && (
				<ul className="space-y-2 mb-1">
					{savedItems.map(item => (
						<li
							key={`saved-${item.id}`}
							onClick={() => onItemSelect(`saved-${item.id}`)}
							className={`flex text-[0.8em] items-center justify-between rounded-lg shadow-sm px-3 py-1 cursor-pointer transition-all duration-200 ${
								selectedItemKey === `saved-${item.id}`
									? "bg-blue-800 border-blue-500 ring-2 ring-blue-500"
									: "bg-zinc-800 border border-zinc-700 hover:bg-zinc-700"
							} ${item.deleted ? 'opacity-60 line-through bg-zinc-900/50' : ''}`}
						>
							<div className="flex items-center gap-2">
								<span className={`font-semibold ${item.deleted ? 'text-zinc-400' : 'text-zinc-100'} truncate max-w-[110px]`}>
									{item.item_name}
								</span>
								{item.deleted && (
									<span className="ml-1 text-xs text-red-400 font-bold">(deleted)</span>
								)}
							</div>
							<div className="flex items-center gap-2">
								<span className={`font-semibold ${item.deleted ? 'text-zinc-500' : 'text-zinc-200'}`}>
									{Number(item.item_price) * Number(item.quantity)}{" "}
									<small>so'm</small>
								</span>
								<span className="inline-block bg-blue-900 text-blue-200 text-xs font-bold rounded-full px-2 py-1 select-none">
									x{item.quantity}
								</span>
								<span className="text-xs text-zinc-400 italic">
									{timeSince(item.u_at)}
								</span>
							</div>
						</li>
					))}
				</ul>
			)}
			{newItems.length > 0 && (
				<>
					<div className="text-xs text-blue-400 mb-1">
						New Items (not saved yet)
					</div>
					<ul className="space-y-2">
						{newItems.map(item => (
							<li
								key={`new-${item.item_name}__${item.item_price}`}
								onClick={() => onItemSelect(`${item.item_name}__${item.item_price}`)}
								className={`flex text-[0.8em] items-center justify-between rounded-lg shadow-sm px-2 py-1 cursor-pointer transition-all duration-200 ${
									selectedItemKey === `${item.item_name}__${item.item_price}`
										? "bg-blue-800 border-blue-500 ring-2 ring-blue-500"
										: "bg-zinc-800 border border-zinc-700 hover:bg-zinc-700"
								}`}
							>
								<div className="flex items-center gap-2">
									<span className="font-semibold text-zinc-100 truncate max-w-[110px]">
										{item.item_name}
									</span>
								</div>
								<div className="flex items-center gap-2">
									<span className="font-semibold text-zinc-200">
										{item.total_price} <small>so'm</small>
									</span>
									<span className="inline-block bg-blue-900 text-blue-200 text-sm font-bold rounded-full px-2 py-1">
										x{item.quantity}
									</span>
								</div>
							</li>
						))}
					</ul>
				</>
			)}
		</div>
	);
}

export default OrderItemsList;
