const categories = [
	{key: "frequent", label: "FREQUENTLY USED"},
	{key: "mains", label: "MAINS"},
	{key: "salads", label: "SALADS"},
	{key: "drinks", label: "DRINKS"},
	{key: "deserts", label: "DESERTS"},
	{key: "appetizers", label: "APPETIZERS"},
];

function MenuComponent({
	menuItems,
	activeTab,
	onTabChange,
	search,
	onSearchChange,
	onAddItem,
	isEditable,
}) {
	let filteredMenuItems = [];
	if (search.trim() !== "") {
		filteredMenuItems = menuItems.filter(item =>
			item.name.toLowerCase().includes(search.toLowerCase())
		);
	} else {
		filteredMenuItems = menuItems.filter(item => {
			if (activeTab === "frequent") return item.is_frequent;
			return item.category === activeTab;
		});
	}

	return (
		<div className="w-full md:w-2/3 flex flex-col min-h-[500px] bg-zinc-900">
			<div className="flex bg-zinc-800 border-b border-zinc-700">
				{categories.map(cat => (
					<button
						key={cat.key}
						className={`flex-1 py-2 text-xs font-bold border-b-4 ${
							activeTab === cat.key
								? "border-blue-500 bg-zinc-900 text-blue-400"
								: "border-transparent text-zinc-400"
						}`}
						onClick={() => onTabChange(cat.key)}
					>
						{cat.label}
					</button>
				))}
			</div>
			<div className="p-2 border-b border-zinc-800 bg-zinc-900">
				<div className="relative">
					<input
						className="w-full p-1 rounded border border-zinc-700 bg-zinc-800 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-400 pr-10"
						placeholder="Search..."
						value={search}
						onChange={e => onSearchChange(e.target.value)}
					/>
					{search && (
						<button
							type="button"
							className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-red-400 text-lg px-1"
							onClick={() => onSearchChange("")}
							tabIndex={0}
							aria-label="Clear search"
						>
							×
						</button>
					)}
				</div>
			</div>
			<div className="flex-1 grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-1 p-4 bg-zinc-900 overflow-y-auto">
				{filteredMenuItems.length === 0 ? (
					<div className="col-span-full text-zinc-500 text-center py-4">
						No menu items found.
					</div>
				) : (
					filteredMenuItems.map(item => (
						<div
							key={item.id}
							className={`rounded-lg shadow text-zinc-100 flex items-center text-center justify-center text-xs font-bold bg-blue-700 transition p-1 w-20 h-20 select-none cursor-pointer ${
								isEditable
									? "hover:bg-blue-500"
									: "opacity-60 cursor-not-allowed"
							}`}
							onClick={() => isEditable && onAddItem(item)}
							tabIndex={0}
							aria-disabled={!isEditable}
						>
							{item.name}
						</div>
					))
				)}
			</div>
		</div>
	);
}

export default MenuComponent;
