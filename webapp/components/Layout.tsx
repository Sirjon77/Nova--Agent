"use client";

import Link from "next/link";
import { useRouter } from "next/router";

/**
 * Layout component used across the Nova Agent dashboard pages.
 *
 * This component renders a simple navigation bar at the top of the
 * application with links to the major sections (Dashboard, Tasks,
 * Reports and Settings) and provides a logout button that clears
 * stored credentials. All pages wrapped with this layout benefit from
 * consistent styling and navigation. The children are rendered inside
 * a main container below the nav bar.
 */
export default function Layout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  /**
   * Clears persisted auth tokens and navigates back to the login page.
   */
  const handleLogout = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("nova_token");
      localStorage.removeItem("nova_role");
    }
    router.push("/login");
  };
  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <nav className="bg-white shadow flex items-center justify-between px-4 py-2">
        <div className="flex space-x-4 text-sm font-medium">
          <Link href="/dashboard" className="hover:underline">
            Dashboard
          </Link>
          <Link href="/tasks" className="hover:underline">
            Tasks
          </Link>
          <Link href="/reports" className="hover:underline">
            Reports
          </Link>
          <Link href="/settings" className="hover:underline">
            Settings
          </Link>
        </div>
        <button
          onClick={handleLogout}
          className="text-gray-600 hover:text-black text-sm"
        >
          Logout
        </button>
      </nav>
      <main className="flex-1 p-4">{children}</main>
    </div>
  );
}