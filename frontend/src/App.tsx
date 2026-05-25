import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { lazy, Suspense } from 'react';
import MainLayout from './layouts/MainLayout';
import ErrorBoundary from './components/ErrorBoundary';
import Spinner from './components/Spinner';
import Button from './components/Button';

const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const TaskListPage = lazy(() => import('./pages/TaskListPage'));
const TaskDetailPage = lazy(() => import('./pages/TaskDetailPage'));
const NotePage = lazy(() => import('./pages/NotePage'));
const MindmapPage = lazy(() => import('./pages/MindmapPage'));
const ImageNotesPage = lazy(() => import('./pages/ImageNotesPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

function PageLoader() {
  return <Spinner className="min-h-[400px]" />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-center" toastOptions={{ duration: 3000 }} />
      <Routes>
        <Route element={<MainLayout />}>
          <Route index element={<Suspense fallback={<PageLoader />}><ErrorBoundary><DashboardPage /></ErrorBoundary></Suspense>} />
          <Route path="tasks" element={<Suspense fallback={<PageLoader />}><ErrorBoundary><TaskListPage /></ErrorBoundary></Suspense>} />
          <Route path="tasks/:taskId" element={<Suspense fallback={<PageLoader />}><ErrorBoundary><TaskDetailPage /></ErrorBoundary></Suspense>} />
          <Route path="notes/:taskId" element={<Suspense fallback={<PageLoader />}><ErrorBoundary><NotePage /></ErrorBoundary></Suspense>} />
          <Route path="notes/:taskId/mindmap" element={<Suspense fallback={<PageLoader />}><ErrorBoundary><MindmapPage /></ErrorBoundary></Suspense>} />
          <Route path="notes/:taskId/images" element={<Suspense fallback={<PageLoader />}><ErrorBoundary><ImageNotesPage /></ErrorBoundary></Suspense>} />
          <Route path="settings" element={<Suspense fallback={<PageLoader />}><ErrorBoundary><SettingsPage /></ErrorBoundary></Suspense>} />
          <Route path="*" element={
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <h1 className="text-6xl font-bold text-gray-200 mb-4">404</h1>
              <p className="text-lg text-text-secondary mb-6">页面不存在</p>
              <Link to="/"><Button variant="primary">返回首页</Button></Link>
            </div>
          } />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
