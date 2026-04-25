import { Outlet, NavLink } from "react-router-dom";
import { Mic, Key, Home } from "lucide-react";

export default function Layout() {
  const nav = "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors";
  const active = "bg-brand-500 text-white";
  const inactive = "text-gray-400 hover:text-white hover:bg-gray-800";

  return (
    <div className="flex h-screen">
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col gap-1 p-3">
        <div className="flex items-center gap-2 px-2 py-3 mb-4">
          <Mic className="text-brand-500" size={22} />
          <span className="font-bold text-lg tracking-tight">WebFlyx Voice</span>
        </div>
        <NavLink to="/voices" className={({ isActive }) => `${nav} ${isActive ? active : inactive}`}>
          <Home size={16} /> Voices
        </NavLink>
        <NavLink to="/settings/keys" className={({ isActive }) => `${nav} ${isActive ? active : inactive}`}>
          <Key size={16} /> API Keys
        </NavLink>
      </aside>
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
