import './App.css';
import { useEffect, useState } from 'react';
import { fetchItems } from './api';
import {Item} from './api-types/components/schemas.d';

function App() {
  const [items, setItems] = useState<Item[] | undefined> ([]);

  useEffect(() => {
    fetchItems().then((data) => {
      setItems(data);
    });
  }, []);

  return (
    <div id="root">
      <h1>Warehouse Inventory</h1>
      {items && items?.length > 0 ? (
        <div className="card">
          {items.map((item) => (
            <div key={item.id} className="item">
              <h2>{item.name}</h2>
              <p>{item.description}</p>
              <p>Price: ${item.price}</p>
              <p>Stock: {item.stock}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="no-data">No data found</p>
      )}
    </div>
  );
}

export default App;
