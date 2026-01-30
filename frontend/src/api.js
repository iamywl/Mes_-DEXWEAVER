import axios from 'axios';

const API_URL = 'http://localhost:8000'; // Adjust as per your FastAPI service URL

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
