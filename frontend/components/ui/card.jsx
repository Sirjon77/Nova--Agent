import React from 'react';
export const Card = ({ children, className='' }) => (
  <div className={`bg-gray-800 rounded-md p-4 shadow ${className}`}>{children}</div>
);
export const CardContent = ({ children }) => <div>{children}</div>;