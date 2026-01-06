import { useAuth } from "./context/AuthContext";
import { Login } from "./views";
import { Outlet, useNavigate } from "react-router-dom";
import { BottomBar } from "./components";
import { useEffect, useRef } from "react";

function App() {
	const { user, loading } = useAuth();
	const navigate = useNavigate();
	const userRef = useRef(user);

	useEffect(() => {
		const wasLoggedIn = !!userRef.current;
		const isLoggedIn = !!user;

		// If the user was not logged in, but now they are, navigate to home.
		if (!wasLoggedIn && isLoggedIn) {
			navigate("/");
		}

		// Update the ref for the next render.
		userRef.current = user;
	}, [user, navigate]);

	if (loading) {
		return <div className="text-zinc-300 p-10 text-center min-h-screen bg-zinc-900">Loading app...</div>;
	}

	if (!user) {
		return (
			<div className="min-h-screen bg-zinc-900">
				<Login />
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-zinc-900">
			<Outlet />
			<BottomBar />
		</div>
	);
}

export default App;
