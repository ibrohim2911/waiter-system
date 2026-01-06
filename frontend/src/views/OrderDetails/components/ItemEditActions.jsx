import React from 'react';
import { DocumentDuplicateIcon, ScissorsIcon, TrashIcon, XMarkIcon, ArrowPathIcon } from '@heroicons/react/24/solid';

const ItemEditActions = ({ item, onCopy, onCut, onDelete, onRestore, onClose }) => {
  const buttonClass = "bg-zinc-700 hover:bg-zinc-600 text-white font-bold p-2 rounded-lg transition-colors duration-200 flex items-center justify-center";

  return (
    <div className="bg-zinc-800 p-2 border-t border-b border-zinc-700 flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex-grow min-w-0">
          <p className={`text-sm font-semibold ${item.deleted ? 'text-zinc-400 line-through' : 'text-white'} truncate`}>{item.item_name}</p>
          <p className="text-xs text-zinc-400">Quantity: {item.quantity}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onCopy} className={buttonClass} aria-label="Copy item">
            <DocumentDuplicateIcon className="h-5 w-5" />
          </button>
          <button onClick={onCut} className={buttonClass} aria-label="Cut/Split item">
            <ScissorsIcon className="h-5 w-5" />
          </button>
          {item.deleted ? (
            <button onClick={onRestore} className="bg-green-700 hover:bg-green-600 text-white font-bold p-2 rounded-lg transition-colors duration-200" aria-label="Restore item">
              <ArrowPathIcon className="h-5 w-5" />
            </button>
          ) : (
            <button onClick={onDelete} className="bg-red-800 hover:bg-red-700 text-white font-bold p-2 rounded-lg transition-colors duration-200" aria-label="Delete item">
              <TrashIcon className="h-5 w-5" />
            </button>
          )}
        </div>
        <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors" aria-label="Close edit actions">
          <XMarkIcon className="h-6 w-6" />
        </button>
      </div>
    </div>
  );
};

export default ItemEditActions;