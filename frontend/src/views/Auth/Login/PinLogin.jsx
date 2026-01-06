import Numpad from "./Numpad";

const PinLogin = ({pinFormik}) => {
	return (
		<form
			className="w-full flex flex-col items-center"
			onSubmit={pinFormik.handleSubmit}
		>
			<input
				name="pin"
				type="password"
				inputMode="numeric"
				pattern="[0-9]*"
				placeholder="PIN"
				className="border rounded px-3 py-2 text-center tracking-widest text-2xl mb-2"
				value={pinFormik.values.pin}
				readOnly
			/>
			<Numpad
				onInput={num =>
					pinFormik.setFieldValue(
						"pin",
						(pinFormik.values.pin + num).slice(0, 4)
					)
				}
				onDelete={() =>
					pinFormik.setFieldValue("pin", pinFormik.values.pin.slice(0, -1))
				}
				onClear={() => pinFormik.setFieldValue("pin", "")}
			/>
			<button
				type="submit"
				className="bg-blue-600 text-white rounded text-lg font-bold tracking-widest py-4 mt-4 w-full hover:bg-blue-700"
			>
				Enter
			</button>
		</form>
	);
};

export default PinLogin;
