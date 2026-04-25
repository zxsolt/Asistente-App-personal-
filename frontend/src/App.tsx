import { Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from '@/pages/AuthPage';
import HomePage from '@/pages/HomePage';
import AssistantPage from '@/pages/AssistantPage';
import NotesPage from '@/pages/NotesPage';
import WeekPage from '@/pages/WeekPage';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function App() {
  return (
    <Routes>
      <Route path="/auth" element={<AuthPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/assistant" element={<AssistantPage />} />
        <Route path="/notes" element={<NotesPage />} />
        <Route path="/week/:id" element={<WeekPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
