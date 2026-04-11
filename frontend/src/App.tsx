import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './components/Layout/MainLayout';
import Dashboard from './pages/Dashboard';
import Trends from './pages/Trends';
import DataTable from './pages/DataTable';
import Measurements from './pages/Measurements';
import Reports from './pages/Reports';
import Devices from './pages/Devices';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/data" element={<DataTable />} />
          <Route path="/devices" element={<Devices />} />
          <Route path="/measurements" element={<Measurements />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
