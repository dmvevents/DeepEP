import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import axios from 'axios';

interface TenantTheme {
  name: string;
  slug: string;
  logo_url: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
  };
  contact: {
    email: string;
    phone: string;
    website: string;
  };
}

interface TenantThemeContextValue {
  theme: TenantTheme;
  loading: boolean;
  error: string | null;
  refreshTheme: () => Promise<void>;
}

const defaultTheme: TenantTheme = {
  name: 'Mortgage Calculator',
  slug: 'default',
  logo_url: '',
  colors: {
    primary: '#667eea',
    secondary: '#10b981',
    accent: '#764ba2',
  },
  contact: {
    email: '',
    phone: '',
    website: '',
  },
};

const TenantThemeContext = createContext<TenantThemeContextValue | undefined>(undefined);

export const useTenantTheme = () => {
  const context = useContext(TenantThemeContext);
  if (!context) {
    throw new Error('useTenantTheme must be used within TenantThemeProvider');
  }
  return context;
};

interface TenantThemeProviderProps {
  children: ReactNode;
}

export const TenantThemeProvider: React.FC<TenantThemeProviderProps> = ({ children }) => {
  const [theme, setTheme] = useState<TenantTheme>(defaultTheme);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTheme = async () => {
    try {
      setLoading(true);
      setError(null);

      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await axios.get(`${API_BASE_URL}/api/tenants/current/`);

      setTheme(response.data.theme_config || response.data);
    } catch (err) {
      console.error('Failed to load tenant theme:', err);
      setError('Failed to load theme');
      // Fall back to default theme on error
      setTheme(defaultTheme);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTheme();
  }, []);

  const refreshTheme = async () => {
    await fetchTheme();
  };

  return (
    <TenantThemeContext.Provider value={{ theme, loading, error, refreshTheme }}>
      {children}
    </TenantThemeContext.Provider>
  );
};
