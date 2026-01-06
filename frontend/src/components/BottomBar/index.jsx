
import React, { useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { HomeIcon, PlusCircleIcon, ArrowLeftOnRectangleIcon, ArrowUturnLeftIcon, UserIcon } from "@heroicons/react/24/outline";


const BottomBar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  // const { logout } = useAuth(); // logout function from context

  // if (location.pathname === "/") {
  //   return null;
  // }

  const goBack = () => {
    navigate(-1);
  };

  const isActive = (path) => location.pathname === path;

  return (
    <div className="fixed bottom-0 left-0 w-full max-h-15 bg-zinc-900 border-t border-zinc-800 flex justify-around items-center py-1 z-[1000]">
      <button
        onClick={() => navigate("/")}
        className={`flex flex-col items-center text-base px-4 py-2 rounded-lg transition-all
          ${isActive("/") ? "bg-blue-500 text-white font-bold shadow-lg" : "text-zinc-100 hover:text-blue-400"}`}
      >
        <HomeIcon className="h-6 w-6 mb-1" />
        Orders
      </button>
      <button
        onClick={() => navigate("/create-order")}
        className={`flex flex-col items-center text-base px-4 py-2 rounded-lg transition-all
          ${isActive("/create-order") ? "bg-blue-500 text-white font-bold shadow-lg" : "text-zinc-100 hover:text-blue-400"}`}
      >
        <PlusCircleIcon className="h-6 w-6 mb-1" />
        Create Order
      </button>
      <button
        onClick={() => navigate("logout")}
        className="flex flex-col items-center text-zinc-100 text-base px-4 py-2 hover:text-blue-400 transition-colors"
      >
        <ArrowLeftOnRectangleIcon className="h-6 w-6 mb-1" />
        Log Out
      </button>
      <button
        onClick={goBack}
        className="flex flex-col items-center text-zinc-100 text-base px-4 py-2 hover:text-blue-400 transition-colors"
      >
        <ArrowUturnLeftIcon className="h-6 w-6 mb-1" />
        Back
      </button>
      <Link to={"/profile"} className={`flex flex-col items-center text-base px-4 py-2 rounded-lg transition-all
          ${isActive("/profile") ? "bg-blue-500 text-white font-bold shadow-lg" : "text-zinc-100 hover:text-blue-400"}`}>
        <UserIcon className="h-6 w-6 mb-1" />
        Profile
      </Link >
    </div>
  );
}
export default BottomBar;