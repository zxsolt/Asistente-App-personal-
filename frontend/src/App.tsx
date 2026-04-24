import { Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from '@/pages/AuthPage';
import HomePage from '@/pages/HomePage';
import WeekPage from '@/pages/WeekPage';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function App() {
  return (
    <Routes>
      <Route path="/auth" element={<AuthPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/week/:id" element={<WeekPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
