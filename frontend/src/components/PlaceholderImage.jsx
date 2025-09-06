import React from 'react';

const PlaceholderImage = ({ width = 60, height = 60, alt = "Government of India", className = "" }) => {
  return (
    <div 
      className={`bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center ${className}`}
      style={{ width: `${width}px`, height: `${height}px` }}
    >
      <div className="text-white font-bold text-lg">
        {alt === "Government of India" ? "GoI" : "IMG"}
      </div>
    </div>
  );
};

export default PlaceholderImage;
