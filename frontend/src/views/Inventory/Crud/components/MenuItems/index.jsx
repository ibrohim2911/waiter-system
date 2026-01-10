import React, { useEffect, useState } from "react";
import { getMenuItems, createMenuItem, editMenuItem, deleteMenuItem } from "../../../../../services/menuItems";
import { getPrinters } from "../../../../../services/printers";

const EmptyState = ({ text }) => (
  <div className="px-4 py-6 text-zinc-400 text-center">{text}</div>
);

const categoryChoices = [
    { value: 'salads', label: 'salatlar' },
    { value: 'mains', label: 'asosiy ovqatlar' },
    { value: 'deserts', label: 'shirinliklar' },
    { value: 'drinks', label: 'ichimliklar' },
    { value: 'appetizers', label: 'yengil ovqatlar' },
];

const MenuItems = () => {
  const [items, setItems] = useState([]);
  const [printers, setPrinters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: "", description: "", price: 0, category: "", is_available: true, is_frequent: false, printer: "" });

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    Promise.all([getMenuItems(), getPrinters()])
      .then(([menuItemsData, printersData]) => {
        if (!mounted) return;
        setItems(Array.isArray(menuItemsData) ? menuItemsData : []);
        setPrinters(Array.isArray(printersData) ? printersData : []);
      })
      .catch((err) => setError(err?.message || "Failed to load data"))
      .finally(() => mounted && setLoading(false));
    return () => (mounted = false);
  }, []);

  const handleChange = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const openCreate = () => {
    setEditing(null);
    setForm({ name: "", description: "", price: 0, category: "", is_available: true, is_frequent: false, printer: "" });
    setShowModal(true);
  };

  const openEdit = (it) => {
    setEditing(it);
    setForm({
      name: it.name || "",
      description: it.description || "",
      price: it.price ?? 0,
      category: it.category || "",
      is_available: it.is_available ?? true,
      is_frequent: it.is_frequent ?? false,
      printer: it.printer || "",
    });
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e && e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      if (editing) {
        const payload = { id: editing.id, ...form };
        const updated = await editMenuItem(payload);
        setItems((prev) => prev.map((p) => (String(p.id) === String(updated.id) ? updated : p)));
      } else {
        const payload = { ...form };
        const created = await createMenuItem(payload);
        setItems((prev) => [created, ...prev]);
      }
      setShowModal(false);
      setEditing(null);
    } catch (err) {
      setError(err?.message || "Failed to save menu item");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (it) => {
    const ok = window.confirm(`Delete menu item ${it.name || it.id}?`);
    if (!ok) return;
    try {
      await deleteMenuItem(it.id);
      setItems((prev) => prev.filter((p) => String(p.id) !== String(it.id)));
    } catch (err) {
      setError(err?.message || "Failed to delete menu item");
    }
  };

  return (
    <div className="mt-8" onClick={() => setMobileOpen((s) => !s)}>
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold">Menu narsalari</h2>
          <button
            className="md:hidden px-2 py-1 bg-zinc-700 hover:bg-zinc-600 text-white rounded text-sm"
            onClick={() => setMobileOpen((s) => !s)}
          >
            {mobileOpen ? 'Hide list' : 'Show list'}
          </button>
        </div>
        <button onClick={openCreate} className="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded text-sm">narsa qoshish</button>
      </div>

      {/* Desktop */}
      <div className="hidden md:block overflow-x-auto bg-zinc-800 rounded-lg border border-zinc-700">
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="text-zinc-300 text-xs uppercase tracking-wider">
              <th className="px-4 py-3">nomi</th>
              <th className="px-4 py-3">turi</th>
              <th className="px-4 py-3">narxi</th>
              <th className="px-4 py-3">Printer</th>
              <th className="px-4 py-3">mavjudligi</th>
              <th className="px-4 py-3">tez-tez ishlatilishi</th>
              <th className="px-4 py-3">harakatlar</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="px-4 py-6 text-zinc-300 text-center">yuklanmoqda...</td></tr>
            ) : error ? (
              <tr><td colSpan={7} className="px-4 py-6 text-red-400 text-center">{error}</td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-6 text-zinc-400 text-center">hech narsa topilmadi.</td></tr>
            ) : (
              items.map((it) => (
                <tr key={it.id} className="border-t border-zinc-700 hover:bg-zinc-900">
                  <td className="px-4 py-3 text-zinc-200">{it.name}</td>
                  <td className="px-4 py-3 text-zinc-200">{it.category}</td>
                  <td className="px-4 py-3 text-zinc-200">{it.price}</td>
                  <td className="px-4 py-3 text-zinc-200">{it.printer_details?.name}</td>
                  <td className="px-4 py-3 text-zinc-200">{it.is_available ? 'Yes' : 'No'}</td>
                  <td className="px-4 py-3 text-zinc-200">{it.is_frequent ? 'Yes' : 'No'}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button onClick={() => openEdit(it)} className="px-2 py-1 text-sm bg-yellow-600 hover:bg-yellow-500 text-white rounded">tahrirlash</button>
                      <button onClick={() => handleDelete(it)} className="px-2 py-1 text-sm bg-red-600 hover:bg-red-500 text-white rounded">o'chirish</button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile */}
      {mobileOpen && (
        <div className="block md:hidden space-y-3">
        {loading ? (
          <EmptyState text="Loading..." />
        ) : error ? (
          <EmptyState text={error} />
        ) : items.length === 0 ? (
          <EmptyState text="No menu items found." />
        ) : (
          items.map((it) => (
            <div key={it.id} className="bg-zinc-800 border border-zinc-700 rounded-lg p-3">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-zinc-200 font-semibold">{it.name}</div>
                  <div className="text-zinc-400 text-xs">{it.category} • {it.price}</div>
                </div>
                <div className="text-right text-xs text-zinc-400">
                  <div>{it.is_available ? 'Available' : 'Not available'}</div>
                  <div>{it.is_frequent ? 'Frequent' : ''}</div>
                </div>
              </div>
              <div className="mt-3 text-zinc-300 text-sm">{String(it.description || '').slice(0, 120)}</div>
              <div className="mt-3 flex gap-2 justify-end">
                <button onClick={() => openEdit(it)} className="px-2 py-1 text-sm bg-yellow-600 hover:bg-yellow-500 text-white rounded">tahrirlash</button>
                <button onClick={() => handleDelete(it)} className="px-2 py-1 text-sm bg-red-600 hover:bg-red-500 text-white rounded">o'chirish</button>
              </div>
            </div>
          ))
        )}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/60" onClick={() => { setShowModal(false); setEditing(null); }} />
          <form onSubmit={handleSave} className="relative z-10 w-full max-w-md bg-zinc-900 rounded-lg border border-zinc-700 p-5 mx-4">
            <h3 className="text-lg font-semibold mb-3">{editing ? 'Edit Menu Item' : 'Add Menu Item'}</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-zinc-300 text-xs mb-1">nomi</label>
                <input value={form.name} onChange={(e) => handleChange('name', e.target.value)} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
              </div>
              <div>
                <label className="block text-zinc-300 text-xs mb-1">turi</label>
                <select
                  value={form.category}
                  onChange={(e) => handleChange('category', e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm"
                >
                  <option value="">turini tanlang</option>
                  {categoryChoices.map(choice => (
                    <option key={choice.value} value={choice.value}>{choice.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-zinc-300 text-xs mb-1">Printer</label>
                <select
                  value={form.printer}
                  onChange={(e) => handleChange('printer', e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm"
                >
                  <option value="">Select Printer</option>
                  {printers.map(printer => (
                    <option key={printer.id} value={printer.id}>{printer.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-300 text-xs mb-1">narxi</label>
                  <input type="number" value={form.price} onChange={(e) => handleChange('price', Number(e.target.value))} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
                </div>
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" className="w-4 h-4" checked={form.is_available} onChange={(e) => handleChange('is_available', e.target.checked)} />
                    <span className="text-zinc-300">mavjudligi</span>
                  </label>
                </div>
              </div>
              <div>
                <label className="block text-zinc-300 text-xs mb-1">qo'shimcha ma'lumot</label>
                <textarea value={form.description} onChange={(e) => handleChange('description', e.target.value)} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" rows={3} />
              </div>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" className="w-4 h-4" checked={form.is_frequent} onChange={(e) => handleChange('is_frequent', e.target.checked)} />
                  <span className="text-zinc-300">tez-tez ishlatilishi</span>
                </label>
              </div>

              {error && <div className="text-red-400 text-sm">{error}</div>}

              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => { setShowModal(false); setEditing(null); }} className="px-3 py-1 rounded bg-zinc-700 text-sm">bekor qilish</button>
                <button type="submit" disabled={saving} className="px-3 py-1 rounded bg-green-600 hover:bg-green-500 text-white text-sm">{saving ? 'Saving...' : (editing ? 'Save' : 'Create')}</button>
              </div>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default MenuItems;
