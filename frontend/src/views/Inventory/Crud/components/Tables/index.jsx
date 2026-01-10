import React, { useEffect, useState } from "react";
import { getAllTables, createTable, editTable, deleteTable } from "../../../../../services/tables";

const EmptyState = ({ text }) => (
  <div className="px-4 py-6 text-zinc-400 text-center">{text}</div>
);

const Tables = () => {
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingTable, setEditingTable] = useState(null);
  const [form, setForm] = useState({
    name: "",
    location: "",
    capacity: 1,
    commission: "",
    is_available: true,
  });

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getAllTables()
      .then((data) => {
        if (!mounted) return;
        setTables(Array.isArray(data) ? data : []);
      })
      .catch((err) => setError(err?.message || "Failed to load tables"))
      .finally(() => mounted && setLoading(false));
    return () => (mounted = false);
  }, []);

  const handleChange = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const openCreate = () => {
    setEditingTable(null);
    setForm({ name: "", location: "", capacity: 1, commission: "", is_available: true });
    setShowModal(true);
  };

  const openEdit = (t) => {
    setEditingTable(t);
    setForm({
      name: t.name || "",
      location: t.location || "",
      capacity: t.capacity ?? 1,
      commission: t.commission || "",
      is_available: t.is_available ?? true,
    });
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e && e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      if (editingTable) {
        const payload = { id: editingTable.id, ...form };
        const updated = await editTable(payload);
        setTables((prev) => prev.map((p) => (String(p.id) === String(updated.id) ? updated : p)));
      } else {
        const payload = { ...form };
        const created = await createTable(payload);
        setTables((prev) => [created, ...prev]);
      }
      setShowModal(false);
      setEditingTable(null);
    } catch (err) {
      setError(err?.message || "Failed to save table");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (t) => {
    const ok = window.confirm(`Delete table ${t.name || t.id}?`);
    if (!ok) return;
    try {
      await deleteTable(t.id);
      setTables((prev) => prev.filter((p) => String(p.id) !== String(t.id)));
    } catch (err) {
      setError(err?.message || "Failed to delete table");
    }
  };

  return (
    <div className="mt-8" onClick={() => setMobileOpen((s) => !s)}>
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold">Stollar</h2>
          <button
            className="md:hidden px-2 py-1 bg-zinc-700 hover:bg-zinc-600 text-white rounded text-sm"
            onClick={() => setMobileOpen((s) => !s)}
          >
            {mobileOpen ? 'Hide list' : 'Show list'}
          </button>
        </div>
        <button onClick={openCreate} className="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded text-sm">Stol qo'shish</button>
      </div>

      {/* Desktop table */}
      <div className="hidden md:block overflow-x-auto bg-zinc-800 rounded-lg border border-zinc-700">
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="text-zinc-300 text-xs uppercase tracking-wider">
              <th className="px-4 py-3">nomi(raqami)</th>
              <th className="px-4 py-3">joylashuvi</th>
              <th className="px-4 py-3">sig'imi</th>
              <th className="px-4 py-3">xizmat haqi</th>
              <th className="px-4 py-3">mavjudligi</th>
              <th className="px-4 py-3">harakatlar</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-zinc-300 text-center">yuklanmoqda...</td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-red-400 text-center">{error}</td>
              </tr>
            ) : tables.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-zinc-400 text-center">stollar topilmadi.</td>
              </tr>
            ) : (
              tables.map((t) => (
                <tr key={t.id} className="border-t border-zinc-700 hover:bg-zinc-900">
                  <td className="px-4 py-3 text-zinc-200">{t.name}</td>
                  <td className="px-4 py-3 text-zinc-200">{t.location}</td>
                  <td className="px-4 py-3 text-zinc-200">{t.capacity}</td>
                  <td className="px-4 py-3 text-zinc-200">{t.commission}</td>
                  <td className="px-4 py-3 text-zinc-200">{t.is_available ? "Yes" : "No"}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button onClick={() => openEdit(t)} className="px-2 py-1 text-sm bg-yellow-600 hover:bg-yellow-500 text-white rounded">tahrirlash</button>
                      <button onClick={() => handleDelete(t)} className="px-2 py-1 text-sm bg-red-600 hover:bg-red-500 text-white rounded">o'chirish</button>
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
        ) : tables.length === 0 ? (
          <EmptyState text="No tables found." />
        ) : (
          tables.map((t) => (
            <div key={t.id} className="bg-zinc-800 border border-zinc-700 rounded-lg p-3">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-zinc-200 font-semibold">{t.name}</div>
                  <div className="text-zinc-400 text-xs">{t.location}</div>
                </div>
                <div className="text-right text-xs text-zinc-400">
                  <div>sig'imi: {t.capacity}</div>
                  <div>{t.is_available ? 'Available' : 'Not available'}</div>
                </div>
              </div>
              <div className="mt-3 text-zinc-300 text-sm">{String(t.commission || '').slice(0,120)}</div>
              <div className="mt-3 flex gap-2 justify-end">
                <button onClick={() => openEdit(t)} className="px-2 py-1 text-sm bg-yellow-600 hover:bg-yellow-500 text-white rounded">tahrirlash</button>
                <button onClick={() => handleDelete(t)} className="px-2 py-1 text-sm bg-red-600 hover:bg-red-500 text-white rounded">o'chirish</button>
              </div>
            </div>
          ))
        )}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/60" onClick={() => { setShowModal(false); setEditingTable(null); }} />
          <form onSubmit={handleSave} className="relative z-10 w-full max-w-md bg-zinc-900 rounded-lg border border-zinc-700 p-5 mx-4">
            <h3 className="text-lg font-semibold mb-3">{editingTable ? 'Edit Table' : 'Add Table'}</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-zinc-300 text-xs mb-1">nomi</label>
                <input value={form.name} onChange={(e) => handleChange('name', e.target.value)} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
              </div>
              <div>
                <label className="block text-zinc-300 text-xs mb-1">joylashuvi</label>
                <input value={form.location} onChange={(e) => handleChange('location', e.target.value)} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-zinc-300 text-xs mb-1">sig'imi</label>
                  <input type="number" value={form.capacity} onChange={(e) => handleChange('capacity', Number(e.target.value))} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
                </div>
                <div>
                  <label className="block text-zinc-300 text-xs mb-1">xizmat haqi</label>
                  <input value={form.commission} onChange={(e) => handleChange('commission', e.target.value)} className="w-full px-3 py-2 bg-zinc-800 rounded border border-zinc-700 text-white text-sm" />
                </div>
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" className="w-4 h-4" checked={form.is_available} onChange={(e) => handleChange('is_available', e.target.checked)} />
                    <span className="text-zinc-300">mavjudligi</span>
                  </label>
                </div>
              </div>

              {error && <div className="text-red-400 text-sm">{error}</div>}

              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => { setShowModal(false); setEditingTable(null); }} className="px-3 py-1 rounded bg-zinc-700 text-sm">bekor qilish</button>
                <button type="submit" disabled={saving} className="px-3 py-1 rounded bg-green-600 hover:bg-green-500 text-white text-sm">{saving ? 'Saving...' : (editingTable ? 'Save' : 'Create')}</button>
              </div>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default Tables;
