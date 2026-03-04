/**
 * AppRouter — React Router v7 setup with lazy-loaded pages.
 * NFR-001: Frontend modularization — replaces monolithic App.jsx.
 */
import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import { LoadingSpinner } from './components/ui';

import {
  Dashboard, Items, BOM, Process, Equipment, Plans, WorkOrders,
  Quality, Inventory, AICenter, Reports, SPC, CAPA, OEE,
  Notification, LotTrace, Barcode, EWI, NCR, Disposition,
  KPI, CMMS, Recipe, Sensor, DMS, Labor, ERP, OPCUA,
  Audit, Resource, MSA, FMEA, Energy, Calibration, SQM,
  Dispatch, SetupMatrix, Costing, DashBuilder, RptBuilder,
  Batch, ECM, ComplexRouting, Multisite, Network, Infra, Login,
} from './pages';

const ProtectedRoutes = () => {
  const {authReady} = useAuth();
  if (!authReady) return <Navigate to="/login" replace />;

  return (
    <Layout>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route index element={<Dashboard />} />
          <Route path="items" element={<Items />} />
          <Route path="bom" element={<BOM />} />
          <Route path="process" element={<Process />} />
          <Route path="equipment" element={<Equipment />} />
          <Route path="plans" element={<Plans />} />
          <Route path="work-orders" element={<WorkOrders />} />
          <Route path="quality" element={<Quality />} />
          <Route path="inventory" element={<Inventory />} />
          <Route path="ai-center" element={<AICenter />} />
          <Route path="reports" element={<Reports />} />
          <Route path="spc" element={<SPC />} />
          <Route path="capa" element={<CAPA />} />
          <Route path="oee" element={<OEE />} />
          <Route path="notification" element={<Notification />} />
          <Route path="lot-trace" element={<LotTrace />} />
          <Route path="barcode" element={<Barcode />} />
          <Route path="ewi" element={<EWI />} />
          <Route path="ncr" element={<NCR />} />
          <Route path="disposition" element={<Disposition />} />
          <Route path="kpi" element={<KPI />} />
          <Route path="cmms" element={<CMMS />} />
          <Route path="recipe" element={<Recipe />} />
          <Route path="sensor" element={<Sensor />} />
          <Route path="dms" element={<DMS />} />
          <Route path="labor" element={<Labor />} />
          <Route path="erp" element={<ERP />} />
          <Route path="opcua" element={<OPCUA />} />
          <Route path="audit" element={<Audit />} />
          <Route path="resource" element={<Resource />} />
          <Route path="msa" element={<MSA />} />
          <Route path="fmea" element={<FMEA />} />
          <Route path="energy" element={<Energy />} />
          <Route path="calibration" element={<Calibration />} />
          <Route path="sqm" element={<SQM />} />
          <Route path="dispatch" element={<Dispatch />} />
          <Route path="setup-matrix" element={<SetupMatrix />} />
          <Route path="costing" element={<Costing />} />
          <Route path="dash-builder" element={<DashBuilder />} />
          <Route path="rpt-builder" element={<RptBuilder />} />
          <Route path="batch" element={<Batch />} />
          <Route path="ecm" element={<ECM />} />
          <Route path="complex-routing" element={<ComplexRouting />} />
          <Route path="multisite" element={<Multisite />} />
          <Route path="network" element={<Network />} />
          <Route path="infra" element={<Infra />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </Layout>
  );
};

const AppRouter = () => (
  <AuthProvider>
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/*" element={<ProtectedRoutes />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  </AuthProvider>
);

const LoginPage = () => {
  const {authReady} = useAuth();
  if (authReady) return <Navigate to="/" replace />;
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Login />
    </Suspense>
  );
};

export default AppRouter;
