import React, { useState } from 'react';

const AutoToggle = ({ onChange }) => {
  const [autoMode, setAutoMode] = useState(true);

  const handleToggle = () => {
    const newMode = !autoMode;
    setAutoMode(newMode);
    onChange(newMode);
  };

  return (
    <div className="p-4 bg-gray-100 rounded-xl shadow-md w-fit transition-colors duration-200">
      <label className="flex items-center space-x-2 cursor-pointer transition-colors duration-200">
        <span className="text-sm font-medium text-gray-700 transition-colors duration-200">Auto Mode</span>
        <input
          type="checkbox"
          checked={autoMode}
          onChange={handleToggle}
          className="form-checkbox h-5 w-5 text-blue-600 transition-colors duration-200"
        />
      </label>
    </div>
  );
};

export default AutoToggle;
