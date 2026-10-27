import React, { useState } from 'react';
import { User } from './types';
import { DEMO_USERS } from './services/api';
import { Navbar } from './components/Navbar';
import { WorkerDashboard } from './components/WorkerDashboard';
import { EmployerDashboard } from './components/EmployerDashboard';
import { en } from './translations/en';
import { ta } from './translations/ta';

export function App() {
  const [currentUser, setCurrentUser] = useState<User>(DEMO_USERS[0]);
  const [language, setLanguage] = useState<'en' | 'ta'>('en');

  const t = language === 'ta' ? ta : en;

  const handleToggleLanguage = () => {
    setLanguage(prev => prev === 'en' ? 'ta' : 'en');
  };

  const isEmployerOrAdmin = currentUser.role === 'admin' || currentUser.role === 'supervisor';

  return (
    <div className="min-h-screen bg-canvas flex flex-col">
      {/* Top Navigation */}
      <Navbar
        currentUser={currentUser}
        onSelectUser={setCurrentUser}
        language={language}
        onToggleLanguage={handleToggleLanguage}
        t={t}
      />

      {/* Main Content Area */}
      <main className="flex-1">
        {isEmployerOrAdmin ? (
          <EmployerDashboard user={currentUser} t={t} language={language} />
        ) : (
          <WorkerDashboard user={currentUser} t={t} language={language} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-border py-4 text-center text-xs text-secondary mt-12">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-bold text-navy">FairShift AI</span>
            <span>—</span>
            <span>Prompt Wars 2026 Hackathon</span>
          </div>
          <div className="text-slate-500">
            Aligned with <strong>UN SDG 8: Decent Work & Economic Growth</strong> (Targets 8.5 & 8.8)
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
