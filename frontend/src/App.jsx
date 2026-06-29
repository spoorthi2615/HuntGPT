import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import LogInput from './pages/LogInput';
import PipelineView from './pages/PipelineView';
import AttackHeatmap from './pages/AttackHeatmap';
import MetricsDashboard from './pages/MetricsDashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<LogInput />} />
          <Route path="pipeline" element={<PipelineView />} />
          <Route path="heatmap" element={<AttackHeatmap />} />
          <Route path="metrics" element={<MetricsDashboard />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
