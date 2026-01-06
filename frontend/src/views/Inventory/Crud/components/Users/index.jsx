import React, { useEffect, useState } from "react";
import { getAllUsers, createUser, EditUser, deleteUser } from "../../../../../services/users";

const Indicator = ({ value, label }) => {
	const trueCls = "bg-green-500 ring-4 ring-green-300 shadow-md";
	const falseCls = "bg-red-500 ring-4 ring-red-300 shadow-md";
	return (
		<div className="flex items-center justify-center" title={label}>
			<div
				className={`w-6 h-6 rounded-sm ${value ? trueCls : falseCls}`}
				aria-hidden
			/>
		</div>
	);
};

const safe = (obj, ...keys) => {
	for (let k of keys) {
		if (obj == null) break;
		if (obj[k] !== undefined && obj[k] !== null) return obj[k];
		const snake = k.replace(/[A-Z]/g, (m) => `_${m.toLowerCase()}`);
		if (obj[snake] !== undefined && obj[snake] !== null) return obj[snake];
		const lower = k.toLowerCase();
		if (obj[lower] !== undefined && obj[lower] !== null) return obj[lower];
	}
	return undefined;
};

const boolVal = (obj, ...keys) => {
	const v = safe(obj, ...keys);
	return !!v;
};

const EmptyState = ({ text }) => (
	<div className="px-4 py-6 text-zinc-400 text-center">{text}</div>
);

const Users = () => {
	const [users, setUsers] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);
	const [mobileOpen, setMobileOpen] = useState(false);

	// Modal state
	const [showModal, setShowModal] = useState(false);
	const [creating, setCreating] = useState(false);
	const [editingUser, setEditingUser] = useState(null);
	const [form, setForm] = useState({
		name: "",
		phone: "",
		email: "",
		role: "",
		isStaff: false,
		isActive: true,
		isSuperuser: false,
	});

	useEffect(() => {
		let mounted = true;
		setLoading(true);
		getAllUsers()
			.then((data) => {
				if (!mounted) return;
				setUsers(Array.isArray(data) ? data : []);
			})
			.catch((err) => {
				if (!mounted) return;
				setError(err?.message || "Failed to load users");
			})
			.finally(() => mounted && setLoading(false));
		return () => {
			mounted = false;
		};
	}, []);

	const handleChange = (key, value) => {
		setForm((f) => ({ ...f, [key]: value }));
	};

	const handleCreate = async (e) => {
		e && e.preventDefault();
		setCreating(true);
		setError(null);
		try {
			// If editingUser is set, call EditUser, else createUser
			if (editingUser) {
				const payload = {
					id: editingUser.id,
					name: form.name,
					phone_number: form.phone,
					email: form.email,
					role: form.role,
					is_staff: form.isStaff,
					is_active: form.isActive,
					is_superuser: form.isSuperuser,
				};
				const updated = await EditUser(payload);
				setUsers((prev) => prev.map((u) => (String(u.id) === String(editingUser.id) ? updated : u)));
				setEditingUser(null);
				setShowModal(false);
				setForm({ name: "", phone: "", email: "", role: "",	 isStaff: false, isActive: true, isSuperuser: false });
			} else {
				const payload = {
					name: form.name,
					phone_number: form.phone,
					email: form.email == "" && null,
					role: form.role,
					is_staff: form.isStaff,
					is_active: form.isActive,
					is_superuser: form.isSuperuser,
					pin: form.pin,
				};
				const newUser = await createUser(payload);
				setUsers((prev) => [newUser, ...prev]);
				setShowModal(false);
				setForm({ name: "", phone: "", email: "", role: "", isPinSetted: false, isStaff: false, isActive: true, isSuperuser: false });
			}
		} catch (err) {
			setError(err?.message || "Failed to create user");
		} finally {
			setCreating(false);
		}
	};

	const handleEditClick = (user) => {
		// populate form and open modal for editing
		setEditingUser(user);
		setForm({
			name: safe(user, "name", "username", "full_name", "first_name") || "",
			phone: safe(user, "phone", "phone_number", "mobile") || "",
			email: safe(user, "email") || "",
			role: safe(user, "role", "user_role") || "",
			isStaff: boolVal(user, "isStaff", "is_staff", "staff", "is_waiter"),
			isActive: boolVal(user, "isActive", "is_active", "active"),
			isSuperuser: boolVal(user, "IsSuperuser", "is_superuser", "is_super_admin", "is_superuser"),
		});
		setShowModal(true);
	};

	const handleDelete = async (user) => {
		const ok = window.confirm(`Delete user ${safe(user, "name", "username") || user.id}?`);
		if (!ok) return;
		try {
			await deleteUser(user.id);
			setUsers((prev) => prev.filter((u) => String(u.id) !== String(user.id)));
		} catch (err) {
			setError(err?.message || "Failed to delete user");
		}
	};

	return (
		<div>
			<div className="mb-4 flex items-center justify-between">
				<div className="flex items-center gap-3">
					<h2 className="text-xl font-semibold" onClick={() => setMobileOpen((s) => !s)}>Users</h2>
					<button
						className="md:hidden px-2 py-1 bg-zinc-700 hover:bg-zinc-600 text-white rounded text-sm"
						onClick={() => setMobileOpen((s) => !s)}
					>
						{mobileOpen ? 'Hide list' : 'Show list'}
					</button>
				</div>
				<div className="flex items-center gap-2">
					<button
						onClick={() => setShowModal(true)}
						className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm"
					>
						Add User
					</button>
				</div>
			</div>

			{/* Desktop / tablet: table (md+) */}
			<div className="hidden md:block overflow-x-auto bg-zinc-800 rounded-lg border border-zinc-700">
				<table className="min-w-full text-sm text-left">
					<thead>
							<tr className="text-zinc-300 text-xs uppercase tracking-wider">
							<th className="px-4 py-3">Name</th>
							<th className="px-4 py-3">Phone</th>
							<th className="px-4 py-3">Email</th>
							<th className="px-4 py-3">Role</th>
							<th className="px-4 py-3">IsStaff</th>
							<th className="px-4 py-3">IsActive</th>
							<th className="px-4 py-3">IsSuperuser</th>
							<th className="px-4 py-3">Actions</th>
						</tr>
					</thead>
					<tbody>
						{loading ? (
							<tr>
								<td colSpan={8} className="px-4 py-6 text-zinc-300 text-center">
									Loading...
								</td>
							</tr>
						) : error ? (
							<tr>
								<td colSpan={8} className="px-4 py-6 text-red-400 text-center">
									{error}
								</td>
							</tr>
						) : users.length === 0 ? (
							<tr>
								<td colSpan={8} className="px-4 py-6 text-zinc-400 text-center">
									No users found.
								</td>
							</tr>
						) : (
							users.map((u) => {
								const name = safe(u, "name", "username", "full_name", "first_name") || `#${u.id}`;
								const phone = safe(u, "phone", "phone_number", "mobile") || "-";
								const email = safe(u, "email") || "-";
								const role = safe(u, "role", "user_role") || (u?.groups ? (u.groups[0]?.name || "-") : "-");

								const isPinSetted = boolVal(u, "isPinSetted", "is_pin_setted", "is_pin_set", "is_pin");
								const isStaff = boolVal(u, "isStaff", "is_staff", "staff", "is_waiter");
								const isActive = boolVal(u, "isActive", "is_active", "active");
								const isSuperuser = boolVal(u, "IsSuperuser", "is_superuser", "is_super_admin", "is_superuser");

								return (
									<tr key={u.id} className="border-t border-zinc-700 hover:bg-zinc-900">
										<td className="px-4 py-3 text-zinc-200">{name}</td>
										<td className="px-4 py-3 text-zinc-200">{phone}</td>
										<td className="px-4 py-3 text-zinc-200">{email}</td>
										<td className="px-4 py-3 text-zinc-200">{role}</td>
											
										<td className="px-4 py-3">
											<Indicator value={isStaff} label="IsStaff" />
										</td>
										<td className="px-4 py-3">
											<Indicator value={isActive} label="IsActive" />
										</td>
										<td className="px-4 py-3">
											<Indicator value={isSuperuser} label="IsSuperuser" />
										</td>
										<td className="px-4 py-3">
											<div className="flex gap-2">
												<button onClick={() => handleEditClick(u)} className="px-2 py-1 text-sm bg-yellow-600 hover:bg-yellow-500 text-white rounded">Edit</button>
												<button onClick={() => handleDelete(u)} className="px-2 py-1 text-sm bg-red-600 hover:bg-red-500 text-white rounded">Delete</button>
											</div>
										</td>
									</tr>
								);
							})
						)}
					</tbody>
				</table>
			</div>

			{/* Mobile: stacked cards */}
			{mobileOpen && (
				<div className="block md:hidden space-y-3">
				{loading ? (
					<EmptyState text="Loading..." />
				) : error ? (
					<EmptyState text={error} />
				) : users.length === 0 ? (
					<EmptyState text="No users found." />
				) : (
					users.map((u) => {
						const name = safe(u, "name", "username", "full_name", "first_name") || `#${u.id}`;
						const phone = safe(u, "phone", "phone_number", "mobile") || "-";
						const email = safe(u, "email") || "-";
						const role = safe(u, "role", "user_role") || (u?.groups ? (u.groups[0]?.name || "-") : "-");
 
						const isStaff = boolVal(u, "isStaff", "is_staff", "staff", "is_waiter");
						const isActive = boolVal(u, "isActive", "is_active", "active");
						const isSuperuser = boolVal(u, "IsSuperuser", "is_superuser", "is_super_admin", "is_superuser");

						return (
							<div key={u.id} className="bg-zinc-800 border border-zinc-700 rounded-lg p-3">
								<div className="flex justify-between items-start">
									<div>
										<div className="text-zinc-200 font-semibold">{name}</div>
										<div className="text-zinc-400 text-xs">{role}</div>
									</div>
									<div className="text-right text-xs text-zinc-400">
										<div>{phone}</div>
										<div>{email}</div>
									</div>
								</div>
								<div className="mt-3 grid grid-cols-4 gap-2">
 									<div className="flex flex-col items-center">
										<Indicator value={isStaff} label="IsStaff" />
										<div className="text-zinc-300 text-xs mt-1">Staff</div>
									</div>
									<div className="flex flex-col items-center">
										<Indicator value={isActive} label="IsActive" />
										<div className="text-zinc-300 text-xs mt-1">Active</div>
									</div>
									<div className="flex flex-col items-center">
										<Indicator value={isSuperuser} label="IsSuperuser" />
										<div className="text-zinc-300 text-xs mt-1">Super</div>
									</div>
								</div>
								<div className="mt-3 flex gap-2 justify-end">
									<button onClick={() => handleEditClick(u)} className="px-2 py-1 text-sm bg-yellow-600 hover:bg-yellow-500 text-white rounded">Edit</button>
									<button onClick={() => handleDelete(u)} className="px-2 py-1 text-sm bg-red-600 hover:bg-red-500 text-white rounded">Delete</button>
								</div>
							</div>
						);
					})
				)}
			</div>
		)}

			{/* Modal */}
			{showModal && (
				<div className="fixed inset-0 z-50 flex items-center justify-center">
					<div className="absolute inset-0 bg-black/60" onClick={() => { setShowModal(false); setEditingUser(null); }} />
					<form
						onSubmit={handleCreate}
						className="relative z-10 w-full max-w-md bg-zinc-900 rounded-lg border border-zinc-700 p-5 mx-4"
					>
						<h3 className="text-lg font-semibold mb-3">{editingUser ? "Edit User" : "Add User"}</h3>
						<div className="space-y-3">
							<div>
								<label className="block text-zinc-300 text-xs mb-1">Name</label>
								<input value={form.name} onChange={(e) => handleChange("name", e.target.value)} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
							</div>
							<div>
								<label className="block text-zinc-300 text-xs mb-1">Phone</label>
								<input value={form.phone} onChange={(e) => handleChange("phone", e.target.value)} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
							</div>
							<div>
								<label className="block text-zinc-300 text-xs mb-1">Email</label>
								<input value={form.email} onChange={(e) => handleChange("email", e.target.value)} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
							</div>
							<div>
								<label className="block text-zinc-300 text-xs mb-1">Role</label>
								<select id="role" value={form.role} onChange={(e) => handleChange("role", e.target.value)} name="role" className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm">
									  <option value="admin">Admin</option>
									  <option value="waiter">Waiter</option>
									  <option value="accountant">accountant</option>
								</select>
								<label className="block text-zinc-300 text-xs mb-1">pin</label>
								<input type="text" value={form.pin} onChange={(e) => handleChange("pin", e.target.value)} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm"/>
							</div>

							<div className="grid grid-cols-2 gap-3">
 
								<label className="flex items-center gap-2 text-sm">
									<input type="checkbox" className="w-4 h-4" checked={form.isStaff} onChange={(e) => handleChange("isStaff", e.target.checked)} />
									<span className="text-zinc-300">IsStaff</span>
								</label>
								<label className="flex items-center gap-2 text-sm">
									<input type="checkbox" className="w-4 h-4" checked={form.isActive} onChange={(e) => handleChange("isActive", e.target.checked)} />
									<span className="text-zinc-300">IsActive</span>
								</label>
								<label className="flex items-center gap-2 text-sm">
									<input type="checkbox" className="w-4 h-4" checked={form.isSuperuser} onChange={(e) => handleChange("isSuperuser", e.target.checked)} />
									<span className="text-zinc-300">IsSuperuser</span>
								</label>
							</div>

							{error && <div className="text-red-400 text-sm">{error}</div>}

							<div className="flex justify-end gap-2 pt-2">
								<button type="button" onClick={() => { setShowModal(false); setEditingUser(null); }} className="px-3 py-1 rounded bg-zinc-700 text-sm">Cancel</button>
								<button type="submit" disabled={creating} className="px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-sm">
									{creating ? (editingUser ? "Saving..." : "Creating...") : (editingUser ? "Save" : "Create")}
								</button>
							</div>
						</div>
					</form>
				</div>
			)}
		</div>
	);
};

export default Users;
