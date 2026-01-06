const Numpad = ({ onInput, onDelete, onClear }) => (
    <div className="grid grid-cols-3 gap-2 mt-4 w-full">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(n => (
            <button
                key={n}
                type="button"
                className="bg-gray-200 rounded py-6 w-full text-xl hover:bg-gray-300"
                onClick={() => onInput(n.toString())}
            >{n}</button>
        ))}
        <button type="button" className="bg-gray-200 rounded py-6 text-xl" onClick={onClear}>C</button>
        <button type="button" className="bg-gray-200 rounded py-6 text-xl" onClick={() => onInput('0')}>0</button>
        <button type="button" className="bg-gray-200 rounded py-6 text-xl" onClick={onDelete}>⌫</button>
    </div>
);

export default Numpad;