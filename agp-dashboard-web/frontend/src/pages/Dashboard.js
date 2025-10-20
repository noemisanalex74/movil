import React, { useState, useEffect } from 'react';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch data from Flask backend
    fetch('/api/dashboard_stats') // Assuming Flask will expose this endpoint
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(error => {
        setError(error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div>Cargando estadísticas...</div>;
  }

  if (error) {
    return <div>Error al cargar estadísticas: {error.message}</div>;
  }

  return (
    <div className="container-fluid mt-4">
      <h1>Resumen General del Dashboard (React)</h1>

      <div className="row">
        <div className="col-md-3 mb-4">
          <div className="card text-white bg-primary shadow-sm">
            <div className="card-body">
              <h5 className="card-title">Total Proyectos</h5>
              <p className="card-text display-4">{stats.total_proyectos}</p>
            </div>
          </div>
        </div>
        <div className="col-md-3 mb-4">
          <div className="card text-white bg-success shadow-sm">
            <div className="card-body">
              <h5 className="card-title">Tareas Pendientes</h5>
              <p className="card-text display-4">{stats.tareas_pendientes}</p>
            </div>
          </div>
        </div>
        <div className="col-md-3 mb-4">
          <div className="card text-white bg-info shadow-sm">
            <div className="card-body">
              <h5 className="card-title">MCPs Registrados</h5>
              <p className="card-text display-4">{stats.mcps_registrados}</p>
            </div>
          </div>
        </div>
        <div className="col-md-3 mb-4">
          <div className="card text-white bg-warning shadow-sm">
            <div className="card-body">
              <h5 className="card-title">Última Tarea Completada</h5>
              <p className="card-text display-4">{stats.ultima_tarea_completada}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Placeholder for charts */}
      <div className="row">
        <div className="col-md-6 mb-4">
          <div className="card shadow-sm">
            <div className="card-header bg-dark text-white">Estadísticas de Proyectos por Estado</div>
            <div className="card-body">
              <p>Gráfico de Proyectos aquí (próximamente)</p>
            </div>
          </div>
        </div>
        <div className="col-md-6 mb-4">
          <div className="card shadow-sm">
            <div className="card-header bg-dark text-white">Estadísticas de Tareas por Prioridad</div>
            <div className="card-body">
              <p>Gráfico de Tareas aquí (próximamente)</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
