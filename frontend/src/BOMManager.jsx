import React, { useState, useEffect } from 'react';

const BOMManager = () => {
    const [partName, setPartName] = useState('');
    const [quantity, setQuantity] = useState(0);
    const [unit, setUnit] = useState('');
    const [parentId, setParentId] = useState(null);
    const [boms, setBoms] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const [showForm, setShowForm] = useState(false);
    const [expandedBoms, setExpandedBoms] = useState({});

    const fetchBoms = async () => {
        setLoading(true);
        setError(null);
        try {
            // Assuming the backend API is exposed at /api/v1/bom/tree relative to the frontend app's origin
            const response = await fetch('/api/v1/bom/tree');
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
            }
            const data = await response.json();
            setBoms(data);
            const initialExpanded = {};
            data.forEach(bom => initialExpanded[bom.id] = false);
            setExpandedBoms(initialExpanded);
        } catch (e) {
            setError(e.message);
            console.error("Failed to fetch BOMs:", e);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateBom = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const newBomData = {
                part_name: partName,
                quantity: parseFloat(quantity),
                unit: unit,
                parent_id: parentId ? parseInt(parentId, 10) : null,
            };
            // Assuming the backend API is exposed at /api/v1/bom relative to the frontend app's origin
            const response = await fetch('/api/v1/bom', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newBomData),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
            }

            setPartName('');
            setQuantity(0);
            setUnit('');
            setParentId(null);
            setShowForm(false);
            fetchBoms();
        } catch (e) {
            setError(e.message);
            console.error("Failed to create BOM:", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBoms();
    }, []);

    const renderBomNode = (bom) => {
        const isExpanded = expandedBoms[bom.id] || false;
        const hasChildren = bom.children && bom.children.length > 0;

        const toggleExpand = () => {
            setExpandedBoms(prev => ({ ...prev, [bom.id]: !prev[bom.id] }));
        };

        return (
            <div key={bom.id} style={{ marginLeft: '20px', borderLeft: '1px solid #ccc', paddingLeft: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
                    {hasChildren && (
                        <button onClick={toggleExpand} style={{ marginRight: '10px', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2em' }}>
                            {isExpanded ? '▼' : '▶'}
                        </button>
                    )}
                    {!hasChildren && <span style={{ marginRight: '10px' }}>•</span>}
                    
                    <strong>{bom.part_name}</strong>
                    <span> (Qty: {bom.quantity} {bom.unit})</span>
                    {bom.parent_id !== null && <span style={{ fontSize: '0.8em', color: '#666' }}> (Parent ID: {bom.parent_id})</span>}
                </div>
                {isExpanded && hasChildren && (
                    <div>
                        {bom.children.map(child => renderBomNode(child))}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div>
            <h2>BOM Management</h2>

            <button onClick={() => setShowForm(!showForm)} style={{ marginBottom: '20px' }}>
                {showForm ? 'Cancel BOM Registration' : 'Register New BOM'}
            </button>

            {showForm && (
                <form onSubmit={handleCreateBom} style={{ marginBottom: '30px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
                    <h3>Register New BOM Item</h3>
                    <div>
                        <label htmlFor="partName">Part Name:</label>
                        <input
                            type="text"
                            id="partName"
                            value={partName}
                            onChange={(e) => setPartName(e.target.value)}
                            required
                            style={{ marginLeft: '10px', marginBottom: '10px' }}
                        />
                    </div>
                    <div>
                        <label htmlFor="quantity">Quantity:</label>
                        <input
                            type="number"
                            id="quantity"
                            value={quantity}
                            onChange={(e) => setQuantity(e.target.value)}
                            required
                            min="0"
                            step="any"
                            style={{ marginLeft: '10px', marginBottom: '10px' }}
                        />
                    </div>
                    <div>
                        <label htmlFor="unit">Unit:</label>
                        <input
                            type="text"
                            id="unit"
                            value={unit}
                            onChange={(e) => setUnit(e.target.value)}
                            required
                            style={{ marginLeft: '10px', marginBottom: '10px' }}
                        />
                    </div>
                    <div>
                        <label htmlFor="parentId">Parent ID (Optional):</label>
                        <input
                            type="number"
                            id="parentId"
                            value={parentId === null ? '' : parentId}
                            onChange={(e) => setParentId(e.target.value === '' ? null : e.target.value)}
                            min="1"
                            style={{ marginLeft: '10px', marginBottom: '10px' }}
                        />
                    </div>
                    <button type="submit" disabled={loading}>
                        {loading ? 'Saving...' : 'Save BOM'}
                    </button>
                </form>
            )}

            <h3>BOM Structure</h3>
            {loading && <p>Loading BOMs...</p>}
            {error && <p style={{ color: 'red' }}>Error: {error}</p>}
            {!loading && !error && boms.length === 0 && <p>No BOMs found. Register a new one.</p>}
            {!loading && !error && boms.length > 0 && (
                <div>
                    {boms.map(bom => renderBomNode(bom))}
                </div>
            )}
        </div>
    );
};

export default BOMManager;
