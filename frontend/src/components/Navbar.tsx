import React from 'react';
import { Shield, Building2, GraduationCap, UserCheck, Languages, Sparkles } from 'lucide-react';
import { User } from '../types';
import { DEMO_USERS } from '../services/api';
import { VoiceAssistant } from './VoiceAssistant';

interface NavbarProps {
  currentUser: User;
  onSelectUser: (u: User) => void;
  language: 'en' | 'ta';
  onToggleLanguage: () => void;
  t: Record<string, string>;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentUser,
  onSelectUser,
  language,
  onToggleLanguage,
  t,
}) => {
  const isConstruction = currentUser.organization_industry === 'construction';

  return (
    <header className="bg-navy text-white sticky top-0 z-50 border-b border-navy-light shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand & SDG Badge */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal flex items-center justify-center text-white shadow-sm font-bold text-xl">
            FS
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight">FairShift AI</span>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-teal text-white">
                SDG 8
              </span>
            </div>
            <p className="text-xs text-slate-300 hidden sm:block">
              {t.tagline}
            </p>
          </div>
        </div>

        {/* Industry Configuration Badge */}
        <div className="hidden md:flex items-center gap-2 bg-navy-dark px-3 py-1.5 rounded-lg border border-navy-light">
          {isConstruction ? (
            <Building2 className="w-4 h-4 text-teal" />
          ) : (
            <GraduationCap className="w-4 h-4 text-teal" />
          )}
          <span className="text-xs font-medium text-slate-200">
            {isConstruction ? 'Construction Sector' : 'Higher Education & Schools'}
          </span>
          <span className="text-[11px] text-teal-300 font-semibold pl-1 border-l border-slate-700">
            {currentUser.organization_name}
          </span>
        </div>

        {/* Controls: Persona Switcher, Language, Voice */}
        <div className="flex items-center gap-3">
          {/* Voice Assistant */}
          <VoiceAssistant language={language} />

          {/* Language Toggle */}
          <button
            onClick={onToggleLanguage}
            className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-navy-dark hover:bg-slate-800 border border-slate-700 text-slate-200 transition-colors"
            title="Toggle English / Tamil"
          >
            <Languages className="w-3.5 h-3.5 text-teal" />
            <span>{language === 'en' ? 'தமிழ்' : 'English'}</span>
          </button>

          {/* Persona Switcher Dropdown */}
          <div className="relative">
            <select
              value={currentUser.id}
              onChange={(e) => {
                const selected = DEMO_USERS.find(u => u.id === Number(e.target.value));
                if (selected) onSelectUser(selected);
              }}
              className="text-xs font-medium bg-teal text-white pl-2 pr-6 py-1.5 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-teal-light appearance-none"
            >
              <optgroup label="🏗️ Construction Sector">
                <option value="4">👷 Ravi Kumar (Worker - Crane Specialist)</option>
                <option value="2">👔 Marcus Vance (Admin/Director)</option>
              </optgroup>
              <optgroup label="🎓 College & Schools Sector">
                <option value="8">🔬 Ananya Sharma (Worker - Lab Instructor)</option>
                <option value="6">🏛️ Dr. Eleanor Vance (Dean of Operations)</option>
              </optgroup>
            </select>
          </div>

          {/* Current Role Pill */}
          <div className="hidden lg:flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium bg-slate-800 text-slate-300">
            <UserCheck className="w-3.5 h-3.5 text-teal" />
            <span className="capitalize">{currentUser.role}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
