import React, { useState, useEffect } from 'react';
import { XMarkIcon, PlusIcon, MinusIcon } from '@heroicons/react/24/solid';
import Numpad from '../../../components/Numpad';

const NewItemEditActions = ({ item, onQuantityChange, onDelete, onClose, onNumpadChange, onNumpadClose }) => {
  const buttonClass = "bg-zinc-700 hover:bg-zinc-600 text-white font-bold p-2 rounded-lg transition-colors duration-200 flex items-center justify-center";
  const [isNumpadOpen, setIsNumpadOpen] = useState(false);
  const [numpadValue, setNumpadValue] = useState(String(item.quantity));

  // Sync numpadValue with item.quantity prop when it changes from the parent
  useEffect(() => {
    console.log(`[NewItemEditActions] useEffect triggered because item.quantity changed. Prop: ${item.quantity}, Current state: ${numpadValue}`);
    if (String(item.quantity) !== numpadValue) {
      console.log(`[NewItemEditActions] useEffect is now syncing state from ${numpadValue} to ${String(item.quantity)}.`);
      setNumpadValue(String(item.quantity));
    }
  }, [item.quantity]);

  console.log(`[NewItemEditActions] Rendering for item: ${item.item_name}, quantity: ${item.quantity}, numpadValue state: ${numpadValue}`);
  
  return (
    <div className="bg-zinc-800 p-2 border-t border-b border-zinc-700 flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex-grow min-w-0">
          <p className="text-sm font-semibold text-white truncate">{item.item_name}</p>
          <p className="text-xs text-zinc-400">Quantity: {item.quantity}</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <div 
            className="text-center text-xl font-mono bg-zinc-700 text-white p-2 rounded min-w-[40px] cursor-pointer"
            onClick={() => {
              console.log(`[NewItemEditActions] Numpad opened. Initializing numpad with current quantity: ${item.quantity}`);
              setNumpadValue(String(item.quantity)); // Re-sync on open
              setIsNumpadOpen(true);
            }}
          >
            {item.quantity}
          </div>
          <button onClick={() => onQuantityChange(-1)} className={buttonClass} aria-label="Decrease quantity">
            <MinusIcon className="h-5 w-5" />
          </button>
          <button onClick={() => onQuantityChange(1)} className={buttonClass} aria-label="Increase quantity">
            <PlusIcon className="h-5 w-5" />
          </button>
          <button onClick={onDelete} className="bg-red-800 hover:bg-red-700 text-white font-bold p-2 rounded-lg transition-colors duration-200" aria-label="Delete item">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
        <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors" aria-label="Close edit actions">
          <XMarkIcon className="h-6 w-6" />
        </button>
      </div>
      {isNumpadOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => {
          console.log('[NewItemEditActions] Backdrop clicked. Closing numpad without applying changes.');
          onNumpadClose?.(); // Call onNumpadClose if it exists
          setIsNumpadOpen(false);
        }}>
          <div onClick={e => e.stopPropagation()}>
            <Numpad
              value={numpadValue}
              onChange={(newValue) => {
                console.log(`[NewItemEditActions] Numpad onChange. Old value: "${numpadValue}", New value: "${newValue}"`);
                setNumpadValue(newValue);
              }}
              onClose={() => {
                console.log(`[NewItemEditActions] Numpad closing. Calling onNumpadChange with value: "${numpadValue}" (type: ${typeof numpadValue})`);
                onNumpadClose?.(); // Also call onNumpadClose if it exists
                onNumpadChange(numpadValue);
                setIsNumpadOpen(false);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default NewItemEditActions;