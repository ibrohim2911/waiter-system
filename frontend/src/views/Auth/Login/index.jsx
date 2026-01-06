import {useFormik} from "formik";
import {useNavigate} from "react-router";
import {useEffect, useState} from "react";
import {loginSchema} from "../../../schemas";
import {useLogin, usePinLogin} from "../../../services/login";
import Numpad from "./Numpad";
import PassLogin from "./PassLogin";
import PinLogin from "./PinLogin";

const Login = () => {
	// const signIn = useSignIn();
	const goPage = useNavigate();
	const [mode, setMode] = useState("pin"); // 'login' or 'pin'
	const login = useLogin();
	const pinLogin = usePinLogin();
	const navigate = page => {
		goPage(page);
	};

	const onSubmit = async (values, actions) => {
		try {
			navigate("/");
			await login(values.phone, values.password);
			navigate("/");
			actions.resetForm();
		} catch (error) {
			throw new Error("error: " + error.message);
		}

		actions.resetForm();
	};

	const {
		values,
		errors,
		touched,
		isSubmitting,
		handleBlur,
		handleChange,
		resetForm,
		handleSubmit,
	} = useFormik({
		initialValues: {
			phone: "1",
			password: "1",
		},
		onSubmit,
		validationSchema: loginSchema,
	});

	// PIN formik
	const pinFormik = useFormik({
		initialValues: {pin: ""},
		onSubmit: async (values, actions) => {
			// PIN submit logic here
			// Example: navigate('/') if PIN is correct
			try {
				navigate("/");
				await pinLogin(values.pin);
				navigate("/");
				actions.resetForm();
			} catch (error) {
				console.error("PIN login failed:", error);
			}
		},
	});

	return (
		<div className="w-screen min-h-screen relative z-[999] top-0 left-0 flex justify-center md:justify-end items-center">
			{/* Background image only on md and up */}
			<div
				className="hidden md:block absolute inset-0 z-0"
				style={{
					backgroundImage: `
                    linear-gradient(
                        to right,
                        rgba(0,0,0,0) 0%,
                        rgba(0,0,0,0) 50%,
                        rgba(0,0,0,0.6) 70%,
                        rgba(0,0,0,0.85) 100%
                    ),
                    url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1500&q=80')
                `,
					backgroundSize: "cover",
					backgroundPosition: "center",
					backgroundRepeat: "no-repeat",
				}}
			/>
			{/* Responsive form container */}
			<div className="relative z-10 bg-white bg-opacity-100 md:bg-opacity-90 rounded-none md:rounded-lg shadow-none md:shadow-lg p-6 md:p-12 w-full h-screen md:h-auto max-w-md mx-0 md:mx-24 flex flex-col items-center min-h-[420px] md:min-h-[600px] justify-center">
				<div className="flex mb-6 w-full">
					<button
						className={`flex-1 py-2 rounded-l ${
							mode === "pin"
								? "bg-blue-600 text-white"
								: "bg-gray-200 text-gray-700"
						}`}
						onClick={() => setMode("pin")}
					>
						PIN
					</button>
					<button
						className={`flex-1 py-2 rounded-r ${
							mode === "login"
								? "bg-blue-600 text-white"
								: "bg-gray-200 text-gray-700"
						}`}
						onClick={() => setMode("login")}
					>
						Login
					</button>
				</div>
				{mode === "login" ? (
					<PassLogin
						errors={errors}
						touched={touched}
						values={values}
						isSubmitting={isSubmitting}
						handleBlur={handleBlur}
						handleChange={handleChange}
						handleSubmit={handleSubmit}
					/>
				) : (
					<PinLogin pinFormik={pinFormik} />
				)}
			</div>
		</div>
	);
};

export default Login;
