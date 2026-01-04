const TableCard = ({ table, onSelect }) => {
	const handleClick = () => {
		onSelect(table);
	};

	return (
		<div
			onClick={handleClick}
			className={`
				cursor-pointer rounded-lg p-4 
				border-2 hover:shadow-lg transition-all duration-200
				aspect-square flex flex-col justify-center
				${table.is_available 
					? "bg-zinc-800 border-zinc-600 hover:border-zinc-500 hover:bg-zinc-700" 
					: "bg-red-900/20 border-red-600 hover:border-red-500 hover:bg-red-900/50"
				}
			`}
		>
			<div className="text-center">
				<h4 className="text-zinc-100 font-bold text-lg mb-2">
					{table.name}
				</h4>
				<p className="text-zinc-400 text-sm mb-2">
					{table.capacity} kishi
				</p>
				<div
					className={`
						text-xs px-2 py-1 rounded-full
						${table.is_available
							? "bg-green-900 text-green-200"
							: "bg-red-900 text-red-200"
						}
					`}
				>
					{table.is_available ? "Bo'sh" : "Band"}
				</div>
				{table.commission && (
					<p className="text-zinc-500 text-xs mt-1">
						Komissiya: {table.commission}%
					</p>
				)}
			</div>
		</div>
	);
};

export default TableCard;