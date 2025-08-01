import React from 'react';
export const Button = ({ children, className='', ...props }) => (
  <button className={`bg-blue-600 hover:bg-blue-500 transition-colors duration-200 px-3 py-2 rounded-md ${className}`} {...props}>
    {children}
  </button>
);