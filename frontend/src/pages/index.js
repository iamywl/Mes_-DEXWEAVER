/**
 * Page exports — lazy-loaded for code splitting.
 */
import { lazy } from 'react';

// Core pages (custom implementations)
export const Dashboard = lazy(() => import('./Dashboard'));
export const Items = lazy(() => import('./Items'));
export const Equipment = lazy(() => import('./Equipment'));
export const Plans = lazy(() => import('./Plans'));
export const WorkOrders = lazy(() => import('./WorkOrders'));
export const Quality = lazy(() => import('./Quality'));
export const Inventory = lazy(() => import('./Inventory'));

// Generated list pages
export const BOM = lazy(() => import('./BOM'));
export const Process = lazy(() => import('./Process'));
export const AICenter = lazy(() => import('./AICenter'));
export const Reports = lazy(() => import('./Reports'));
export const SPC = lazy(() => import('./SPC'));
export const CAPA = lazy(() => import('./CAPA'));
export const OEE = lazy(() => import('./OEE'));
export const Notification = lazy(() => import('./Notification'));
export const LotTrace = lazy(() => import('./LotTrace'));
export const Barcode = lazy(() => import('./Barcode'));
export const EWI = lazy(() => import('./EWI'));
export const NCR = lazy(() => import('./NCR'));
export const Disposition = lazy(() => import('./Disposition'));
export const KPI = lazy(() => import('./KPI'));
export const CMMS = lazy(() => import('./CMMS'));
export const Recipe = lazy(() => import('./Recipe'));
export const Sensor = lazy(() => import('./Sensor'));
export const DMS = lazy(() => import('./DMS'));
export const Labor = lazy(() => import('./Labor'));
export const ERP = lazy(() => import('./ERP'));
export const OPCUA = lazy(() => import('./OPCUA'));
export const Audit = lazy(() => import('./Audit'));
export const Resource = lazy(() => import('./Resource'));
export const MSA = lazy(() => import('./MSA'));
export const FMEA = lazy(() => import('./FMEA'));
export const Energy = lazy(() => import('./Energy'));
export const Calibration = lazy(() => import('./Calibration'));
export const SQM = lazy(() => import('./SQM'));
export const Dispatch = lazy(() => import('./Dispatch'));
export const SetupMatrix = lazy(() => import('./SetupMatrix'));
export const Costing = lazy(() => import('./Costing'));
export const DashBuilder = lazy(() => import('./DashBuilder'));
export const RptBuilder = lazy(() => import('./RptBuilder'));
export const Batch = lazy(() => import('./Batch'));
export const ECM = lazy(() => import('./ECM'));
export const ComplexRouting = lazy(() => import('./ComplexRouting'));
export const Multisite = lazy(() => import('./Multisite'));
export const Network = lazy(() => import('./Network'));
export const Infra = lazy(() => import('./Infra'));
export const Login = lazy(() => import('./Login'));
