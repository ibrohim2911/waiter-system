import { useEffect } from "react";
import {useAuth} from "../../context/AuthContext";

const LogoutInvisiblePage = () => {
	const {logout} = useAuth();
	useEffect(() => {
		logout();
	});
	return <></>;
};
export default LogoutInvisiblePage;
