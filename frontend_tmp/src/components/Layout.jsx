import React from 'react';
import Navigation from './Navigation';
import './Layout.css';

const Layout = ({ children }) => {
    return (
        <div className="layout">
            <Navigation />
            <main className="main-content">
                {children}
            </main>
        </div>
    );
};

export default Layout;
