import { useAuth } from "../../context/AuthContext";
import Waiter from "./Waiter";
import Admin from "./Admin";
import { useEffect, useState } from "react";
import { me } from "../../services/getMe";

const Profile = () => {
    const { user, loading } = useAuth();
    const [isLoading, setIsLoading] = useState(false)
    const [userData, setUserData] = useState(null)
    useEffect(() => {
        const fetchUserData = async () => {
            try {
                setIsLoading(true);
                const _userData = await me();
                setUserData(_userData);
            } catch (error) {
                console.error("Error fetching user data in Profile component:", error);
            } finally {
                setIsLoading(false);
            }
        }
        fetchUserData();
    },[]);
    console.log(userData);
    
    if (loading || isLoading) return <div className="text-center text-zinc-300 p-10">Loading profile...</div>
    if (!user) return <div className="text-center text-zinc-300 p-10">No user data</div>
    return user?.role === "waiter" ? (<Waiter user={userData} />) : (<Admin user={userData} />)
}

export default Profile