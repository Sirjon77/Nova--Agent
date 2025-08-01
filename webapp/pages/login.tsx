"use client";

import { useState } from "react";
import { useRouter } from "next/router";

/**
 * Login page for Nova Agent dashboard.
 *
 * This page renders a simple username/password form. When the form is
 * submitted, it posts credentials to the backend authentication endpoint
 * (`/api/auth/login`). If the login is successful, the returned JWT token
 * is stored in localStorage and the user is redirected to the dashboard.
 * On failure, an error message is displayed.
 */
export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        throw new Error("Invalid credentials");
      }
      const data = await res.json();
      // Store token and role in localStorage
      localStorage.setItem("nova_token", data.token);
      localStorage.setItem("nova_role", data.role);
      // Redirect to dashboard
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Login failed");
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-4">
      <h1 className="text-2xl font-bold mb-4">Nova Agent Login</h1>
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded shadow-md w-full max-w-sm">
        <label className="block mb-2">
          <span className="text-gray-700">Username</span>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mt-1 block w-full rounded border-gray-300 focus:border-blue-500 focus:ring-blue-500"
            required
          />
        </label>
        <label className="block mb-4">
          <span className="text-gray-700">Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 block w-full rounded border-gray-300 focus:border-blue-500 focus:ring-blue-500"
            required
          />
        </label>
        {error && <p className="text-red-600 mb-2">{error}</p>}
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
        >
          Log in
        </button>
      </form>
    </div>
  );
}