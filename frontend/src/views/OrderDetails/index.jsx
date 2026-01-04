import React, {useEffect, useState, useReducer} from "react";
import {
	useParams,
	useNavigate,
	useLocation,
	useBlocker,
} from "react-router-dom";
import {fetchOrder, updateOrder} from "../../services/orders";
import {
	updateOrderItem,
	deleteOrderItem,
	createOrderItemList,
} from "../../services/orderItems";
import api from "../../services/api";
import {me} from "../../services/getMe";

import OrderHeader from "./components/OrderHeader";
import OrderItemsList from "./components/OrderItemsList";
import OrderTotals from "./components/OrderTotals";
import OrderActions from "./components/OrderActions";
import ItemEditActions from "./components/ItemEditActions";
import NewItemEditActions from "./components/NewItemEditActions";
import MenuComponent from "./components/MenuComponent";
import Numpad from "../../components/Numpad";

const categories = [
	{key: "frequent", label: "FREQUENTLY USED"},
	{key: "mains", label: "MAINS"},
	{key: "salads", label: "SALADS"},
	{key: "drinks", label: "DRINKS"},
	{key: "deserts", label: "DESERTS"},
	{key: "appetizers", label: "APPETIZERS"},
];

const initialState = {
	order: null,
	newOrderItems: [],
	pendingEdits: [],
	selectedItemKey: null,
};

function orderReducer(state, action) {
	switch (action.type) {
		case 'SET_ORDER':
			return { ...state, order: action.payload };
		case 'SET_SELECTED_ITEM':
			return { ...state, selectedItemKey: action.payload };
		case 'ADD_NEW_ITEM': {
			const menuItem = action.payload;
			const idx = state.newOrderItems.findIndex(i => i.menu_item === menuItem.id);
			if (idx !== -1) {
				const updated = [...state.newOrderItems];
				updated[idx] = { ...updated[idx], quantity: updated[idx].quantity + 1 };
				return { ...state, newOrderItems: updated };
			}
			return {
				...state,
				newOrderItems: [...state.newOrderItems, {
					menu_item: menuItem.id,
					item_name: menuItem.name,
					item_price: menuItem.price,
					quantity: 1,
				}]
			};
		}
		case 'ADD_SPLIT_ITEM': {
			const { menuItem, quantity } = action.payload;
			return {
				...state,
				newOrderItems: [...state.newOrderItems, {
					menu_item: menuItem.id,
					item_name: menuItem.name,
					item_price: menuItem.price,
					quantity: quantity,
					unique_id: Date.now() // Ensure it's a unique item and doesn't group
				}]
			};
		}
		case 'CHANGE_ITEM_QUANTITY': {
			const { key, delta } = action.payload;
			if (key.startsWith("saved-")) {
				const itemId = Number(key.replace("saved-", ""));
				const originalItem = state.order.items.find(i => i.id === itemId);
				if (!originalItem) return state;

				const existingEdit = state.pendingEdits.find(e => e.id === itemId);
				const currentQuantity = existingEdit ? existingEdit.quantity : originalItem.quantity;
				const newQuantity = Number(currentQuantity) + delta;

				if (newQuantity > 0) {
					const otherEdits = state.pendingEdits.filter(e => e.id !== itemId);
					return { ...state, pendingEdits: [...otherEdits, { id: itemId, quantity: newQuantity }] };
				} else {
					const otherEdits = state.pendingEdits.filter(e => e.id !== itemId);
					return { ...state, pendingEdits: [...otherEdits, { id: itemId, deleted: true }], selectedItemKey: null };
				}
			} else { // New item
				const totalCurrentQuantity = state.newOrderItems
					.filter(i => `${i.item_name}__${i.item_price}` === key)
					.reduce((sum, i) => sum + i.quantity, 0);
				const newQuantity = totalCurrentQuantity + delta;

				const otherItems = state.newOrderItems.filter(i => `${i.item_name}__${i.item_price}` !== key);
				if (newQuantity > 0) {
					const currentItem = state.newOrderItems.find(i => `${i.item_name}__${i.item_price}` === key);
					return { ...state, newOrderItems: [...otherItems, { ...currentItem, quantity: newQuantity }] };
				} else {
					return { ...state, newOrderItems: otherItems, selectedItemKey: null };
				}
			}
		}
		case 'DELETE_ITEM': {
			const { key } = action.payload;
			if (key.startsWith("saved-")) {
				const itemId = Number(key.replace("saved-", ""));
				const otherEdits = state.pendingEdits.filter(e => e.id !== itemId);
				return { ...state, pendingEdits: [...otherEdits, { id: itemId, deleted: true }], selectedItemKey: null };
			} else {
				return { ...state, newOrderItems: state.newOrderItems.filter(i => `${i.item_name}__${i.item_price}` !== key), selectedItemKey: null };
			}
		}
		case 'RESTORE_ITEM': {
			const { key } = action.payload;
			if (key.startsWith("saved-")) {
				const itemId = Number(key.replace("saved-", ""));
				return { ...state, pendingEdits: state.pendingEdits.filter(e => e.id !== itemId), selectedItemKey: `saved-${itemId}` };
			}
			return state;
		}
		case 'CLEAR_UNSAVED':
			return {
				...state,
				newOrderItems: [], // Clear new items
				pendingEdits: state.pendingEdits.filter(e => !e.deleted), // Revert quantity changes, but not deletions
			};
		case 'SAVE_SUCCESS':
			return {
				...state,
				order: action.payload,
				newOrderItems: [],
				pendingEdits: [],
				selectedItemKey: null,
			};
		default:
			return state;
	}
}

export default function OrderEditPage() {
	const location = useLocation();
	const navigate = useNavigate();
	const params = useParams();
	const [menuItems, setMenuItems] = useState([]);
	const [activeTab, setActiveTab] = useState(categories[0].key);
	const [search, setSearch] = useState("");
	const [user, setUser] = useState(null);
	const [isNumpadOpen, setIsNumpadOpen] = useState(false);
	const [numpadValue, setNumpadValue] = useState("1");
	const [isSplitting, setIsSplitting] = useState(false);
	const [state, dispatch] = useReducer(orderReducer, initialState);
	const { order, newOrderItems, pendingEdits, selectedItemKey } = state;

	const hasUnsavedChanges = newOrderItems.length > 0 || pendingEdits.length > 0;

	const blocker = useBlocker(hasUnsavedChanges);

	useEffect(() => {
		if (blocker.state === "blocked") {
			const saveAndProceed = async () => {
				await handleSave();
				blocker.proceed();
			};

			saveAndProceed();
		}
	}, [blocker]);

	const id = location.state?.orderid || params.orderid;

	const handleSave = async () => {
		try {
			if (newOrderItems.length > 0) {
				await createOrderItemList(
					newOrderItems.map(item => ({
						order: order.id,
						menu_item: item.menu_item,
						quantity: item.quantity,
					}))
				);
			}

			const editPromises = state.pendingEdits
				.map(edit => {
					if (edit.deleted) return deleteOrderItem(edit.id);
					else if (typeof edit.quantity === "number") {
						const original = order.items.find(i => i.id === edit.id);
						if (original)
							return updateOrderItem(edit.id, {
								order: order.id,
								menu_item: original.menu_item,
								quantity: edit.quantity,
							});
					}
					return null;
				})
				.filter(Boolean);

			if (editPromises.length) {
				const results = await Promise.allSettled(editPromises);
				const failedEdits = results.filter(r => r.status === 'rejected');

				results.forEach(result => {
					if (result.status === "rejected") {
						console.error("Failed to process an edit:", result.reason);
					}
				});

				if (failedEdits.length > 0) {
					alert(`Failed to save ${failedEdits.length} changes. The page will refresh, but some changes may not have been saved.`);
				}
			}

			const res = await fetchOrder(state.order.id);
			dispatch({ type: 'SAVE_SUCCESS', payload: res.data });
		} catch (err) {
			console.error("Save failed", err);
			alert("Failed to save order. Please check your connection and try again.");
		}
	};

	const handleUpdateStatus = async status => {
		await updateOrder(order.id, {
			...order,
			order_status: status,
		});
		dispatch({ type: 'SET_ORDER', payload: { ...order, order_status: status } });
		dispatch({ type: 'SET_SELECTED_ITEM', payload: null });
	};

	useEffect(() => {
		me().then(setUser);
	}, []);

	useEffect(() => {
		if (!id) return;
		fetchOrder(id)
			.then(res => dispatch({ type: 'SET_ORDER', payload: res.data }))
			.catch(err => console.error("Error fetching order:", err));
		api
			.get("/menuitems/")
			.then(res => setMenuItems(res.data))
			.catch(err => console.error("Error fetching menu items:", err));
	}, [id]);

	const isEditable =
		order &&
		user &&
		((user.role === "waiter" && order.order_status === "processing") ||
			(user.role !== "waiter" &&
				(order.order_status === "processing" ||
					order.order_status === "pending")));

	const commission = order?.table_details?.commission
		? Number(order.table_details.commission)
		: 0;

	const calcSubtotal = React.useMemo(() => {
		const allItems = [...(order?.items || []), ...newOrderItems];
		return allItems.reduce(
			(sum, item) => sum + Number(item.item_price) * Number(item.quantity),
			0
		);
	}, [order, newOrderItems]);

	const calcAmount = React.useMemo(() => {
		let withCommission = calcSubtotal + (calcSubtotal * commission) / 100;
		return Math.round(withCommission);
	}, [calcSubtotal, commission]);

	const displayedSavedOrderItems = React.useMemo(() => {
		if (!order?.items) return [];
		return order.items
			.map(item => {
				const edit = pendingEdits.find(e => e.id === item.id);
				if (edit) {
					// if deleted, keep it in the list to show as "to be deleted"
					if (edit.deleted) return { ...item, deleted: true };
					return { ...item, quantity: edit.quantity };
				}
				return item;
			});
	}, [order, pendingEdits]);

	const groupedNewOrderItems = React.useMemo(() => {
		if (!newOrderItems.length) return [];
		const map = {};
		newOrderItems.forEach(item => {
			const key = `${item.item_name}__${item.item_price}`;
			if (!map[key]) {
				map[key] = {...item, quantity: 0, total_price: 0};
			}
			map[key].quantity += Number(item.quantity);
			map[key].total_price += Number(item.item_price) * Number(item.quantity);
		});
		return Object.values(map);
	}, [newOrderItems]);

	const handleItemCopy = (key) => {
		if (!isEditable) return;
		const sourceItem = displayedSavedOrderItems.find(i => `saved-${i.id}` === key) || groupedNewOrderItems.find(i => `${i.item_name}__${i.item_price}` === key);
		if (!sourceItem) return;

		const originalMenuItem = menuItems.find(mi => mi.id === sourceItem.menu_item);
		if (originalMenuItem) {
			dispatch({ type: 'ADD_NEW_ITEM', payload: originalMenuItem });
		} else {
			console.error("Could not find original menu item to copy.");
		}
	};

	const handleItemCut = () => {
		if (!selectedItem) return;
		// Open the global numpad to input split quantity
		setNumpadValue(String(selectedItem.quantity || 1));
		setIsNumpadOpen(true);
	};

	const handleSplitConfirm = (splitQuantity) => {
		if (!selectedItem || !selectedItemKey) return;

		const quantityToSplit = parseFloat(splitQuantity);
		if (isNaN(quantityToSplit) || quantityToSplit <= 0) {
			setIsSplitting(false);
			return;
		}

		if (quantityToSplit >= selectedItem.quantity) {
			alert("Split quantity must be less than the item's total quantity.");
			return;
		}

		// Reduce quantity of the original item
		dispatch({ type: 'CHANGE_ITEM_QUANTITY', payload: { key: selectedItemKey, delta: -quantityToSplit } });

		// Add a new item with the split quantity
		const originalMenuItem = menuItems.find(mi => mi.id === selectedItem.menu_item);
		if (originalMenuItem) {
			dispatch({ type: 'ADD_SPLIT_ITEM', payload: { menuItem: originalMenuItem, quantity: quantityToSplit } });
		}
		setIsSplitting(false);
		dispatch({ type: 'SET_SELECTED_ITEM', payload: selectedItemKey }); // Re-select the item
	};

	const selectedItem = selectedItemKey ? (displayedSavedOrderItems.find(i => `saved-${i.id}` === selectedItemKey) || groupedNewOrderItems.find(i => `${i.item_name}__${i.item_price}` === selectedItemKey)) : null;

	if (!id) return <div>No order id provided.</div>;
	if (!order) return <div>Loading order...</div>;

	return (
		<div className="min-h-screen bg-zinc-900 flex items-stretch justify-center p-0 m-0">
			<div
				className="w-full max-w-[100vw] bg-zinc-800 rounded-none shadow-lg flex flex-col md:flex-row overflow-hidden border border-zinc-700"
				style={{height: "calc(100vh - 60px)"}}
			>
				<div className="w-full md:w-1/3 flex flex-col border-r border-zinc-700 bg-zinc-900 min-h-[500px]">
					<OrderHeader
						order={order}
						isEditable={isEditable}
						onNavigate={navigate}
					/>
					<OrderItemsList
						savedItems={displayedSavedOrderItems}
						newItems={groupedNewOrderItems}
						selectedItemKey={selectedItemKey}
						onItemSelect={(key) => dispatch({ type: 'SET_SELECTED_ITEM', payload: key })}
						isSplitting={isSplitting}
					/>
					{isSplitting && selectedItem && (
						<NewItemEditActions
							item={selectedItem}
							onNumpadChange={handleSplitConfirm}
							onNumpadClose={() => setIsSplitting(false)}
							isSplitMode={true}
							startWithNumpadOpen={true}
							useSimpleFormatting={true}
						/>
					)}
					{isNumpadOpen && (
						<Numpad
							value={numpadValue}
							onChange={setNumpadValue}
							onClose={() => {
								// When OK pressed in Numpad, confirm split
								handleSplitConfirm(numpadValue);
								setIsNumpadOpen(false);
							}}
						/>
					)}
					{selectedItem && !isSplitting && isEditable && selectedItemKey.startsWith("saved-") && (
						<ItemEditActions
							item={selectedItem}
							onCopy={() => handleItemCopy(selectedItemKey)}
							onCut={handleItemCut}
							onDelete={() => dispatch({ type: 'DELETE_ITEM', payload: { key: selectedItemKey } })}
							onRestore={() => dispatch({ type: 'RESTORE_ITEM', payload: { key: selectedItemKey } })}
							onQuantityChange={(delta) => dispatch({ type: 'CHANGE_ITEM_QUANTITY', payload: { key: selectedItemKey, delta } })}
							onClose={() => dispatch({ type: 'SET_SELECTED_ITEM', payload: null })}
						/>
					)}
					{selectedItem && !isSplitting && isEditable && !selectedItemKey.startsWith("saved-") && (
						<NewItemEditActions
							item={selectedItem}
							onQuantityChange={(delta) => dispatch({ type: 'CHANGE_ITEM_QUANTITY', payload: { key: selectedItemKey, delta } })}
							onDelete={() => dispatch({ type: 'DELETE_ITEM', payload: { key: selectedItemKey } })}
							onClose={() => dispatch({ type: 'SET_SELECTED_ITEM', payload: null })}
							onNumpadChange={(val) => {
								const newQuantity = parseFloat(val);
								if (!isNaN(newQuantity) && newQuantity > 0) {
									dispatch({ type: 'CHANGE_ITEM_QUANTITY', payload: { key: selectedItemKey, delta: newQuantity - selectedItem.quantity } });
								}
							}}
							onNumpadClose={() => dispatch({ type: 'SET_SELECTED_ITEM', payload: null })}
						/>
					)}
					<OrderTotals
						subtotal={calcSubtotal}
						commission={commission}
						total={calcAmount}
					/>
					<OrderActions
						order={order}
						user={user}
						isEditable={isEditable} 
						onClear={() => dispatch({ type: 'CLEAR_UNSAVED' })}
						onSave={handleSave}
						onUpdateStatus={handleUpdateStatus}
					/>
				</div>
				<MenuComponent
					menuItems={menuItems}
					activeTab={activeTab}
					onTabChange={setActiveTab}
					search={search}
					onSearchChange={setSearch}
					onAddItem={(item) => dispatch({ type: 'ADD_NEW_ITEM', payload: item })}
					isEditable={isEditable}
				/>
			</div>
		</div>
	);
}
