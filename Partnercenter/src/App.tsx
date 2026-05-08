import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import Dashboard from './pages/Dashboard';
import AuthCallbackPage from './pages/AuthCallbackPage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/callback" element={<AuthCallbackPage />} />
          {/* Dashboard handles its own sub-routes */}
          <Route path="/*" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
