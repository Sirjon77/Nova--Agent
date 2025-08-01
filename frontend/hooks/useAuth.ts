import { useState, useEffect } from 'react';
export function useAuth() {
  const [role, setRole] = useState<string | null>(null);
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setRole(payload.role);
    }
  }, []);
  return { role };
}
