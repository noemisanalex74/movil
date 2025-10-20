import React from 'react';

const Layout = ({ children }) => {
  return (
    <div className="d-flex flex-column min-vh-100">
      <header className="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm">
        <div className="container-fluid">
          <a className="navbar-brand" href="#">AGP Dashboard</a>
          {/* Aquí podrías añadir un botón para el sidebar o elementos de navegación */}
        </div>
      </header>
      <div className="d-flex flex-grow-1">
        {/* Sidebar placeholder */}
        <nav className="d-flex flex-column flex-shrink-0 p-3 bg-light" style={{ width: '250px' }}>
          <ul className="nav nav-pills flex-column mb-auto">
            <li className="nav-item"><a href="/" className="nav-link active">Resumen</a></li>
            {/* Más enlaces aquí */}
          </ul>
        </nav>
        {/* Main content */}
        <main className="flex-grow-1 p-3">
          {children}
        </main>
      </div>
      <footer className="bg-dark text-white text-center p-2 mt-auto">
        <p>&copy; 2025 AGP Dashboard</p>
      </footer>
    </div>
  );
};

export default Layout;
