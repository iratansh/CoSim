import { ReactNode } from 'react';

import { useAuth } from '../hooks/useAuth';
import TopNav from './TopNav';

interface Props {
  title: string;
  actions?: ReactNode;
  children: ReactNode;
}

const Layout = ({ title, actions, children }: Props) => {
  const { user } = useAuth();

  return (
    <div className="layout">
      <TopNav userEmail={user?.email} />
      <main>
        <div className="container">
          {actions && (
            <header
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1.5rem'
              }}
            >
              <h1 style={{ margin: 0, fontSize: '1.75rem' }}>{title}</h1>
              {actions}
            </header>
          )}
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
