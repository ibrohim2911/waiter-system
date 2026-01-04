const PassLogin = ({handleSubmit, handleChange, handleBlur, values, errors, touched, isSubmitting}) => {
	return (
		<form className="w-full flex flex-col gap-4" onSubmit={handleSubmit}>
			<input
				name="phone"
				type="tel"
				placeholder="Telefon raqam (998901234567)"
				className="border rounded px-3 py-2"
				value={values.phone}
				onChange={handleChange}
				onBlur={handleBlur}
			/>
			{touched.phone && errors.phone && (
				<div className="text-red-500 text-sm">{errors.phone}</div>
			)}
			<input
				name="password"
				type="password"
				placeholder="Password"
				className="border rounded px-3 py-2"
				value={values.password}
				onChange={handleChange}
				onBlur={handleBlur}
			/>
			{touched.password && errors.password && (
				<div className="text-red-500 text-sm">{errors.password}</div>
			)}
			<button
				type="submit"
				className="bg-blue-600 text-white rounded py-2 mt-2 hover:bg-blue-700 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
				disabled={isSubmitting}
			>
				{isSubmitting && (
					<div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
				)}
				{isSubmitting ? "Kirish..." : "Login"}
			</button>
		</form>
	);
};

export default PassLogin;
