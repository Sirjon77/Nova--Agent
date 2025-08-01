"use client";

import { useEffect } from "react";
import { useRouter } from "next/router";

/**
 * Root page for Nova Agent dashboard. This component checks for an existing
 * JWT token in localStorage. If none is found, it redirects the user to
 * the login page. Otherwise, it redirects to the dashboard overview.
 */
export default function Home() {
  const router = useRouter();
  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("nova_token") : null;
    if (!token) {
      router.replace("/login");
    } else {
      router.replace("/dashboard");
    }
  }, [router]);
  return null;
}