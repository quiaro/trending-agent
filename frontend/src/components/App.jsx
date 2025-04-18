import React, { useState } from 'react';
import Controls from './Controls';
import Content from './Content';
import Header from './Header';

function App() {
  const [trendingData, setTrendingData] = useState('');
  const [loading, setLoading] = useState(false);

  const categories = [
    'Business and Finance',
    'Entertainment',
    'Food and Drink',
    'Games',
    'Health',
    'Hobbies and Leisure',
    'Jobs and Education',
    'Science',
    'Sports',
    'Technology',
  ];

  const fetchTrendingData = async (category) => {
    setLoading(true);
    setTrendingData('');

    try {
      const response = await fetch(
        `/api/trending/${encodeURIComponent(category)}`
      );

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const eventData = text
          .split('\n\n')
          .filter((chunk) => chunk.trim().startsWith('data: '))
          .map((chunk) => chunk.replace('data: ', ''))
          .join('');

        setTrendingData((prev) => prev + eventData);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setTrendingData('Error fetching trending data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <Header />
      <Controls
        categories={categories}
        onSubmit={fetchTrendingData}
        loading={loading}
      />
      <Content data={trendingData} loading={loading} />
    </div>
  );
}

export default App;
