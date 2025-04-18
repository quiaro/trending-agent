import React, { useState } from 'react';

function Controls({ categories, onSubmit, loading }) {
  const [selectedCategory, setSelectedCategory] = useState('');

  const handleCategoryChange = (e) => {
    setSelectedCategory(e.target.value);
  };

  const handleSubmit = () => {
    if (selectedCategory) {
      onSubmit(selectedCategory);
    }
  };

  return (
    <div className="controls">
      <h1>What is trending?</h1>
      <div className="control-row">
        <span className="label">Pick a category:</span>
        <select
          value={selectedCategory}
          onChange={handleCategoryChange}
          disabled={loading}
        >
          <option value="" disabled>
            Select category
          </option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
        <button onClick={handleSubmit} disabled={!selectedCategory || loading}>
          {loading ? (
            <>
              <span className="loading"></span>
              Loading...
            </>
          ) : (
            'Show me trending information'
          )}
        </button>
      </div>
    </div>
  );
}

export default Controls;
