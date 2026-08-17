import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { MainLayout } from './components/layout/MainLayout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { UsersPage } from './pages/UsersPage';
import { BadgePage } from './pages/BadgePage';
import { AssetsPage } from './pages/AssetsPage';
import { ServiceDeskPage } from './pages/ServiceDeskPage';
import { MaintenancePage } from './pages/MaintenancePage';
import { BorrowingsPage } from './pages/BorrowingsPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

const App: React.FC = () => {
  const checkAuth = useAuthStore((state) => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <MainLayout>
                <DashboardPage />
              </MainLayout>
            }
          />
          <Route
            path="/users"
            element={
              <MainLayout>
                <UsersPage />
              </MainLayout>
            }
          />
          <Route
            path="/assets"
            element={
              <MainLayout>
                <AssetsPage />
              </MainLayout>
            }
          />
          <Route
            path="/badge"
            element={
              <MainLayout>
                <BadgePage />
              </MainLayout>
            }
          />
          <Route
            path="/servicos"
            element={
              <MainLayout>
                <ServiceDeskPage />
              </MainLayout>
            }
          />
          <Route
            path="/manutencoes"
            element={
              <MainLayout>
                <MaintenancePage />
              </MainLayout>
            }
          />
          <Route
            path="/emprestimos"
            element={
              <MainLayout>
                <BorrowingsPage />
              </MainLayout>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
