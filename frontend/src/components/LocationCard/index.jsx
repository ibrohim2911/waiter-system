import {useState, useEffect} from "react";

const LocationCard = ({ location, isSelected, onSelect, getTableCount }) => {
	const [tableCount, setTableCount] = useState(0);
	const [isLoading, setIsLoading] = useState(false);

	useEffect(() => {
		const fetchCount = async () => {
			setIsLoading(true);
			try {
				const count = await getTableCount(location);
				setTableCount(count);
			} catch (err) {
				console.error('Error fetching table count:', err);
				setTableCount(0);
			} finally {
				setIsLoading(false);
			}
		};

		fetchCount();
	}, [location, getTableCount]);

	return (
		<div
			onClick={() => onSelect(location)}
			className={`
				cursor-pointer rounded-lg p-4 transition-all duration-200 
				border-2 hover:shadow-lg w-full
				${isSelected
					? "bg-blue-600 border-blue-400 shadow-blue-400/30"
					: "bg-zinc-700 border-zinc-600 hover:border-zinc-500 hover:bg-zinc-600"
				}
			`}
		>
			<h3 className="text-zinc-100 font-semibold text-sm mb-1">
				{location}
			</h3>
			<p className="text-zinc-300 text-xs">
				{isLoading ? 'Yuklanmoqda...' : `${tableCount} ta stol`}
			</p>
		</div>
	);
};

export default LocationCard;