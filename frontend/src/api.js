/**
 * API Service Module
 *
 * Provides centralized API communication services for MES system.
 * Handles requests to manufacturing execution system endpoints with
 * proper error handling and configuration management.
 *
 * @module api
 * @version 1.0.0
 */

import axios from 'axios';

/**
 * API base URL configuration.
 * Can be overridden using REACT_APP_API_URL environment variable.
 * @type {string}
 */
const API_BASE_URL =
  process.env.REACT_APP_API_URL || 'http://192.168.64.5:30461/api';

/**
 * Create axios instance with default configuration.
 * Includes timeout, headers, and interceptors for request/response handling.
 *
 * @type {import('axios').AxiosInstance}
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor for logging and debugging.
 * Logs all outgoing requests for monitoring and troubleshooting.
 */
api.interceptors.request.use(
  (config) => {
    console.debug('[API Request]', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error.message);
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for error handling.
 * Logs all response errors for debugging and monitoring.
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status || 'Unknown';
    const message = error.message || 'Unknown error';
    console.error('[API Response Error]', `Status: ${status}`, message);
    return Promise.reject(error);
  }
);

/**
 * Item Management Service
 *
 * Provides endpoints for managing inventory items including
 * raw materials, semi-finished goods, and finished products.
 *
 * @namespace itemService
 */
export const itemService = {
  /**
   * Fetch all items from inventory.
   *
   * @async
   * @returns {Promise<Array>} Array of all items in inventory
   * @throws {Error} If request fails
   */
  getAllItems: () => api.get('/items/'),

  /**
   * Create a new item in inventory.
   *
   * @async
   * @param {Object} itemData - Item information
   * @param {string} itemData.item_code - Unique item code
   * @param {string} itemData.name - Item name
   * @param {string} itemData.type - Item type (raw material, etc.)
   * @param {string} itemData.unit - Measurement unit
   * @returns {Promise<Object>} Created item data with ID
   * @throws {Error} If request fails
   */
  createItem: (itemData) => api.post('/items/', itemData),
};

/**
 * Production Plan Service
 *
 * Manages production planning including creation and retrieval
 * of manufacturing schedules and targets.
 *
 * @namespace productionPlanService
 */
export const productionPlanService = {
  /**
   * Fetch all production plans.
   *
   * @async
   * @returns {Promise<Array>} Array of production plans
   * @throws {Error} If request fails
   */
  getAllProductionPlans: () => api.get('/production_plans/'),

  /**
   * Create a new production plan.
   *
   * @async
   * @param {Object} planData - Production plan information
   * @param {string} planData.item_code - Item to produce
   * @param {number} planData.quantity - Quantity to produce
   * @returns {Promise<Object>} Created plan data with ID
   * @throws {Error} If request fails
   */
  createProductionPlan: (planData) => api.post('/production_plans/', planData),
};

/**
 * Equipment Management Service
 *
 * Handles equipment inventory and status management for
 * manufacturing facility monitoring.
 *
 * @namespace equipmentService
 */
export const equipmentService = {
  /**
   * Fetch all equipment.
   *
   * @async
   * @returns {Promise<Array>} Array of equipment
   * @throws {Error} If request fails
   */
  getAllEquipments: () => api.get('/equipments/'),

  /**
   * Update equipment status.
   *
   * @async
   * @param {string} equipmentId - Equipment identifier
   * @param {Object} statusData - Status update data
   * @param {string} statusData.status - New equipment status (RUN, IDLE)
   * @returns {Promise<Object>} Updated equipment data
   * @throws {Error} If request fails
   */
  updateEquipmentStatus: (equipmentId, statusData) =>
    api.put(`/equipments/${equipmentId}`, statusData),
};

/**
 * BOM (Bill of Materials) Service
 *
 * Manages product composition information including component
 * relationships and quantity requirements.
 *
 * @namespace bomService
 */
export const bomService = {
  /**
   * Create a new BOM entry.
   *
   * @async
   * @param {Object} bomData - BOM information
   * @param {string} bomData.product_item_code - Product item code
   * @param {string} bomData.component_item_code - Component item code
   * @param {number} bomData.quantity - Component quantity required
   * @returns {Promise<Object>} Created BOM data
   * @throws {Error} If request fails
   */
  createBom: (bomData) => api.post('/bom/', bomData),

  /**
   * Fetch BOM for a specific product.
   *
   * @async
   * @param {string} productItemCode - Product item code
   * @returns {Promise<Object>} BOM information with all components
   * @throws {Error} If request fails
   */
  getBomByProduct: (productItemCode) => api.get(`/bom/${productItemCode}`),
};

export default api;
