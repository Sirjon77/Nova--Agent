import React, { createContext, useContext, useState, useCallback } from 'react';

const DataContext = createContext();

export const DataProvider = ({ children }) => {
  const [cache, setCache] = useState({});

  const fetchData = useCallback(async (key, url) => {
    if (cache[key]) return cache[key];
    try {
      const res = await fetch(url);
      const data = await res.json();
      setCache(prev => ({ ...prev, [key]: data }));
      return data;
    } catch (err) {
      console.error("Fetch failed:", err);
      return null;
    }
  }, [cache]);

  return (
    <DataContext.Provider value={{ cache, fetchData }}>
      {children}
    </DataContext.Provider>
  );
};

export const useData = () => useContext(DataContext);