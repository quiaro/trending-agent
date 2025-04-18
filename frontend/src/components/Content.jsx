import React from 'react';

function Content({ data, loading }) {
  return (
    <div className="content">
      {loading && !data ? (
        <div>Fetching trending information...</div>
      ) : data ? (
        <div>{data}</div>
      ) : (
        <div>
          Select a category and click the button to see trending information.
        </div>
      )}
    </div>
  );
}

export default Content;
