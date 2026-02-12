import axios from 'axios';

const API_URL = 'http://192.168.64.5:30461/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const itemService = {
  getAllItems: () => api.get('/items/'),
  createItem: (itemData) => api.post('/items/', itemData),
};

export const productionPlanService = {
  getAllProductionPlans: () => api.get('/production_plans/'),
  createProductionPlan: (planData) => api.post('/production_plans/', planData),
};

export const equipmentService = {
  getAllEquipments: () => api.get('/equipments/'),
  updateEquipmentStatus: (equipmentId, statusData) => api.put(`/equipments/${equipmentId}`, statusData),
};

export const bomService = {
  createBom: (bomData) => api.post('/bom/', bomData),
  getBomByProduct: (productItemCode) => api.get(`/bom/${productItemCode}`),
};
