import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { KioskProvider } from './context/KioskContext';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import Dashboard from './pages/Dashboard';
import AuthCallbackPage from './pages/AuthCallbackPage';
import FindIdPage from './pages/FindIdPage';
import FindPasswordPage from './pages/FindPasswordPage';

function App() {
  return (
    <AuthProvider>
      <KioskProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/callback" element={<AuthCallbackPage />} />
            <Route path="/find-id" element={<FindIdPage />} />
            <Route path="/find-password" element={<FindPasswordPage />} />
            {/* Dashboard handles its own sub-routes */}
            <Route path="/*" element={<Dashboard />} />
          </Routes>
        </BrowserRouter>
      </KioskProvider>
    </AuthProvider>
  );
}

export default App;
