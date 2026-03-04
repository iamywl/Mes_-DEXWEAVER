/**
 * Barcode page — Barcode generation and scanning.
 * Uses /api/barcode/generate and /api/barcode/scan.
 */
import React, { useState } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { PageHeader, Card, Input, Btn, LoadingSpinner, EmptyState, Badge } from '../components/ui';

const Barcode = () => {
  const [activeTab, setActiveTab] = useState('scan');
  const [scanInput, setScanInput] = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [genInput, setGenInput] = useState('');
  const [genResult, setGenResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const handleScan = async () => {
    if (!scanInput.trim()) {
      showToast('Please enter a barcode value', false);
      return;
    }
    setLoading(true);
    setScanResult(null);
    try {
      const r = await api.post('/api/barcode/scan', { barcode: scanInput.trim() });
      setScanResult(r.data);
      showToast('Barcode scanned successfully');
    } catch (err) {
      showToast('Scan failed', false);
    }
    setLoading(false);
  };

  const handleGenerate = async () => {
    if (!genInput.trim()) {
      showToast('Please enter data to generate barcode', false);
      return;
    }
    setLoading(true);
    setGenResult(null);
    try {
      const r = await api.post('/api/barcode/generate', { data: genInput.trim() });
      setGenResult(r.data);
      showToast('Barcode generated successfully');
    } catch (err) {
      showToast('Generation failed', false);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <PageHeader title="Barcode Management" />

      <div className="flex gap-2">
        {['scan', 'generate'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
              activeTab === tab
                ? 'bg-blue-600 text-white'
                : 'bg-[#1e293b] text-slate-400 hover:text-white border border-slate-700'
            }`}
          >
            {tab === 'scan' ? 'Scan Barcode' : 'Generate Barcode'}
          </button>
        ))}
      </div>

      {activeTab === 'scan' && (
        <div className="space-y-3">
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1">Barcode Value</label>
              <Input
                value={scanInput}
                onChange={e => setScanInput(e.target.value)}
                placeholder="Scan or enter barcode value"
                className="w-full"
                onKeyDown={e => e.key === 'Enter' && handleScan()}
              />
            </div>
            <Btn onClick={handleScan} disabled={loading}>
              {loading ? 'Scanning...' : 'Scan'}
            </Btn>
          </div>
          {scanResult && (
            <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-4">
              <h3 className="text-white text-xs font-bold mb-2">Scan Result</h3>
              <div className="grid grid-cols-2 gap-2 text-xs text-slate-300">
                {Object.entries(scanResult).map(([k, v]) => (
                  <div key={k}>
                    <span className="text-slate-500">{k}: </span>
                    <span className="text-white">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'generate' && (
        <div className="space-y-3">
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1">Data</label>
              <Input
                value={genInput}
                onChange={e => setGenInput(e.target.value)}
                placeholder="Enter data to encode (e.g., LOT number, item code)"
                className="w-full"
                onKeyDown={e => e.key === 'Enter' && handleGenerate()}
              />
            </div>
            <Btn onClick={handleGenerate} disabled={loading}>
              {loading ? 'Generating...' : 'Generate'}
            </Btn>
          </div>
          {genResult && (
            <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-4">
              <h3 className="text-white text-xs font-bold mb-2">Generated Barcode</h3>
              {genResult.barcode_image ? (
                <img src={genResult.barcode_image} alt="Generated barcode" className="max-w-full" />
              ) : (
                <pre className="text-xs text-slate-400 overflow-auto max-h-60">{JSON.stringify(genResult, null, 2)}</pre>
              )}
            </div>
          )}
        </div>
      )}

      {loading && <LoadingSpinner />}
    </div>
  );
};

export default Barcode;
