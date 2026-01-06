import React, { useEffect, useState } from "react";
import {
  getInventoryItems,
  createInventoryItem,
  editInventoryItem,
  deleteInventoryItem,
} from "../../../../../services/inventory";

const EmptyState = ({ text }) => (
  <div className="px-4 py-6 text-zinc-400 text-center">{text}</div>
);

const Items = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [form, setForm] = useState({
    name: "",
    quantity: 0,
    unit_of_measure: "",
    price: 0,
    description: "",
  });

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getInventoryItems()
      .then((data) => {
        if (!mounted) return;
        setItems(Array.isArray(data) ? data : []);
      })
      .catch((err) => setError(err?.message || "Failed to load items"))
      .finally(() => mounted && setLoading(false));
    return () => (mounted = false);
  }, []);

  const handleChange = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const openCreate = () => {
    setEditingItem(null);
    setForm({ name: "", quantity: 0, unit_of_measure: "", price: 0, description: "" });
    setShowModal(true);
  };

  const openEdit = (item) => {
    setEditingItem(item);
    setForm({
      name: item.name || "",
      quantity: item.quantity ?? 0,
      unit_of_measure: item.unit_of_measure || "",
      price: item.price ?? 0,
      description: item.description || "",
    });
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e && e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      if (editingItem) {
        const payload = { id: editingItem.id, ...form };
        const updated = await editInventoryItem(payload);
        setItems((prev) => prev.map((it) => (String(it.id) === String(updated.id) ? updated : it)));
      } else {
        const payload = { ...form };
        const created = await createInventoryItem(payload);
        setItems((prev) => [created, ...prev]);
      }
      setShowModal(false);
      setEditingItem(null);
    } catch (err) {
      setError(err?.message || "Failed to save item");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (item) => {
    const ok = window.confirm(`Delete item ${item.name || item.id}?`);
    if (!ok) return;
    try {
      await deleteInventoryItem(item.id);
      setItems((prev) => prev.filter((it) => String(it.id) !== String(item.id)));
    } catch (err) {
      setError(err?.message || "Failed to delete item");
    }
  };

  return (
    <div className="mt-8">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold" onClick={() => setMobileOpen((s) => !s)}>Inventory Items</h2>
          <button
            className="md:hidden px-2 py-1 bg-zinc-700 hover:bg-zinc-600 text-white rounded text-sm"
            onClick={() => setMobileOpen((s) => !s)}
          >
            {mobileOpen ? 'Hide list' : 'Show list'}
          </button>
        </div>
        <button onClick={openCreate} className="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded text-sm">Add Item</button>
      </div>

      {/* Desktop table */}
      <div className="hidden md:block overflow-x-auto bg-zinc-800 rounded-lg border border-zinc-700">
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="text-zinc-300 text-xs uppercase tracking-wider">
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Quantity</th>
              <th className="px-4 py-3">Unit</th>
              <th className="px-4 py-3">Price</th>
              <th className="px-4 py-3">Description</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-zinc-300 text-center">Loading...</td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-red-400 text-center">{error}</td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-zinc-400 text-center">No items found.</td>
              </tr>
            ) : (
              items.map((it) => (
                <tr key={it.id} className="border-t border-zinc-700 hover:bg-zinc-900">
                  <td className="px-4 py-3 text-zinc-200">{it.name}</td>
                  <td className="px-4 py-3 text-zinc-200">{it.quantity}</td>
                  <td className="px-4 py-3 text-zinc-200">{it.unit_of_measure}</td>
                  <td className="px-4 py-3 text-zinc-200">{it.price}</td>
                  <td className="px-4 py-3 text-zinc-200">{String(it.description || "").slice(0, 60)}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button onClick={() => openEdit(it)} className="px-2 py-1 text-sm bg-yellow-600 hover:bg-yellow-500 text-white rounded">Edit</button>
                      <button onClick={() => handleDelete(it)} className="px-2 py-1 text-sm bg-red-600 hover:bg-red-500 text-white rounded">Delete</button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      {mobileOpen && (
        <div className="block md:hidden space-y-3">
        {loading ? (
          <EmptyState text="Loading..." />
        ) : error ? (
          <EmptyState text={error} />
        ) : items.length === 0 ? (
          <EmptyState text="No items found." />
        ) : (
          items.map((it) => (
            <div key={it.id} className="bg-zinc-800 border border-zinc-700 rounded-lg p-3">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-zinc-200 font-semibold">{it.name}</div>
                  <div className="text-zinc-400 text-xs">{it.unit_of_measure} • {it.price}</div>
                </div>
                <div className="text-right text-xs text-zinc-400">
                  <div>Qty: {it.quantity}</div>
                </div>
              </div>
              <div className="mt-3 text-zinc-300 text-sm">{String(it.description || '').slice(0,120)}</div>
              <div className="mt-3 flex gap-2 justify-end">
                <button onClick={() => openEdit(it)} className="px-2 py-1 text-sm bg-yellow-600 hover:bg-yellow-500 text-white rounded">Edit</button>
                <button onClick={() => handleDelete(it)} className="px-2 py-1 text-sm bg-red-600 hover:bg-red-500 text-white rounded">Delete</button>
              </div>
            </div>
          ))
        )}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/60" onClick={() => { setShowModal(false); setEditingItem(null); }} />
          <form onSubmit={handleSave} className="relative z-10 w-full max-w-md bg-zinc-900 rounded-lg border border-zinc-700 p-5 mx-4">
            <h3 className="text-lg font-semibold mb-3">{editingItem ? 'Edit Item' : 'Add Item'}</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-zinc-300 text-xs mb-1">Name</label>
                <input value={form.name} onChange={(e) => handleChange('name', e.target.value)} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-zinc-300 text-xs mb-1">Quantity</label>
                  <input type="number" value={form.quantity} onChange={(e) => handleChange('quantity', Number(e.target.value))} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
                </div>
                <div>
                  <label className="block text-zinc-300 text-xs mb-1">Unit</label>
                  <input value={form.unit_of_measure} onChange={(e) => handleChange('unit_of_measure', e.target.value)} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
                </div>
                <div>
                  <label className="block text-zinc-300 text-xs mb-1">Price</label>
                  <input type="number" value={form.price} onChange={(e) => handleChange('price', Number(e.target.value))} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
                </div>
              </div>
              <div>
                <label className="block text-zinc-300 text-xs mb-1">Description</label>
                <textarea value={form.description} onChange={(e) => handleChange('description', e.target.value)} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" rows={3} />
              </div>

              {error && <div className="text-red-400 text-sm">{error}</div>}

              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => { setShowModal(false); setEditingItem(null); }} className="px-3 py-1 rounded bg-zinc-700 text-sm">Cancel</button>
                <button type="submit" disabled={saving} className="px-3 py-1 rounded bg-green-600 hover:bg-green-500 text-white text-sm">{saving ? 'Saving...' : (editingItem ? 'Save' : 'Create')}</button>
              </div>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default Items;
