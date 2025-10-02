import { ReactNode, useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface Props {
  children?: ReactNode;
  userEmail?: string | null;
}

// Icons
const UserIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
    <circle cx="12" cy="7" r="4"></circle>
  </svg>
);

const SettingsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="3"></circle>
    <path d="M12 1v6m0 6v6m9-9h-6m-6 0H3"></path>
  </svg>
);

const LogoutIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
    <polyline points="16 17 21 12 16 7"></polyline>
    <line x1="21" y1="12" x2="9" y2="12"></line>
  </svg>
);

const ChevronDownIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="6 9 12 15 18 9"></polyline>
  </svg>
);

const RobotIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="6" y="10" width="12" height="10" rx="2"></rect>
    <path d="M12 10V6"></path>
    <circle cx="12" cy="4" r="2"></circle>
    <circle cx="9" cy="14" r="1"></circle>
    <circle cx="15" cy="14" r="1"></circle>
  </svg>
);

const TopNav = ({ children, userEmail }: Props) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDropdown]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  // Extract initials from email
  const getInitials = (email: string | null | undefined) => {
    if (!email) return 'U';
    const name = email.split('@')[0];
    return name.slice(0, 2).toUpperCase();
  };

  // Get membership tier and styling
  const getMembershipBadge = () => {
    const tier = (user?.plan ?? 'free').toLowerCase();
    
    const badges: Record<string, { label: string; gradient: string; icon: string }> = {
      free: {
        label: 'Free',
        gradient: 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
        icon: '🆓'
      },
      student: {
        label: 'Student',
        gradient: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
        icon: '🎓'
      },
      pro: {
        label: 'Pro',
        gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
        icon: '⚡'
      },
      team: {
        label: 'Team',
        gradient: 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
        icon: '👥'
      },
      enterprise: {
        label: 'Enterprise',
        gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
        icon: '🏢'
      }
    };

    return badges[tier] || badges.free;
  };

  const membershipBadge = getMembershipBadge();

  return (
    <nav
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1rem 1.5rem',
        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        color: '#ffffff',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        position: 'relative',
        zIndex: 100
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
        <Link
          to="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontWeight: 700,
            fontSize: '1.25rem',
            textDecoration: 'none',
            color: 'white',
            transition: 'opacity 0.2s ease'
          }}
          onMouseOver={(e) => e.currentTarget.style.opacity = '0.8'}
          onMouseOut={(e) => e.currentTarget.style.opacity = '1'}
        >
          <RobotIcon />
          CoSim
        </Link>
        
        {userEmail && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <Link
              to="/projects"
              style={{
                color: '#cbd5e1',
                textDecoration: 'none',
                fontWeight: 500,
                transition: 'color 0.2s ease',
                fontSize: '0.9375rem'
              }}
              onMouseOver={(e) => e.currentTarget.style.color = 'white'}
              onMouseOut={(e) => e.currentTarget.style.color = '#cbd5e1'}
            >
              Projects
            </Link>
          </div>
        )}
      </div>

      {userEmail && (
        <div style={{ position: 'relative' }} ref={dropdownRef}>
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '8px',
              padding: '0.5rem 0.75rem',
              color: 'white',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              fontSize: '0.9375rem'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)';
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.3)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
            }}
          >
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 600,
              fontSize: '0.875rem'
            }}>
              {getInitials(userEmail)}
            </div>
            <span style={{ maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {userEmail}
            </span>
            <ChevronDownIcon />
          </button>

          {showDropdown && (
            <div style={{
              position: 'absolute',
              top: 'calc(100% + 0.5rem)',
              right: 0,
              minWidth: '260px',
              background: 'white',
              borderRadius: '12px',
              boxShadow: '0 12px 32px rgba(0, 0, 0, 0.2)',
              border: '1px solid #e2e8f0',
              overflow: 'hidden',
              animation: 'slideDown 0.2s ease'
            }}>
              {/* User Info Header */}
              <div style={{
                padding: '1rem',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                borderBottom: '1px solid rgba(255, 255, 255, 0.2)'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  marginBottom: '0.75rem'
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    background: 'rgba(255, 255, 255, 0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '1rem'
                  }}>
                    {getInitials(userEmail)}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>
                      {userEmail?.split('@')[0]}
                    </div>
                    <div style={{
                      fontSize: '0.8125rem',
                      opacity: 0.9,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {userEmail}
                    </div>
                  </div>
                </div>
                
                {/* Membership Badge */}
                <div style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.375rem 0.75rem',
                  background: membershipBadge.gradient,
                  borderRadius: '20px',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
                  border: '1px solid rgba(255, 255, 255, 0.2)'
                }}>
                  <span style={{ fontSize: '1rem' }}>{membershipBadge.icon}</span>
                  <span>{membershipBadge.label} Plan</span>
                </div>
              </div>

              {/* Menu Items */}
              <div style={{ padding: '0.5rem 0' }}>
                <Link
                  to="/profile"
                  onClick={() => setShowDropdown(false)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.75rem 1rem',
                    color: '#1e293b',
                    textDecoration: 'none',
                    transition: 'background 0.2s ease',
                    fontSize: '0.9375rem'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = '#f8fafc'}
                  onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <UserIcon />
                  <span>Profile</span>
                </Link>

                <Link
                  to="/settings"
                  onClick={() => setShowDropdown(false)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.75rem 1rem',
                    color: '#1e293b',
                    textDecoration: 'none',
                    transition: 'background 0.2s ease',
                    fontSize: '0.9375rem'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = '#f8fafc'}
                  onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <SettingsIcon />
                  <span>Settings</span>
                </Link>

                <div style={{ height: '1px', background: '#e2e8f0', margin: '0.5rem 0' }} />

                <button
                  onClick={handleLogout}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.75rem 1rem',
                    width: '100%',
                    background: 'transparent',
                    border: 'none',
                    color: '#dc2626',
                    cursor: 'pointer',
                    transition: 'background 0.2s ease',
                    fontSize: '0.9375rem',
                    textAlign: 'left'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = '#fef2f2'}
                  onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <LogoutIcon />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {!userEmail && children}

      <style>{`
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </nav>
  );
};

export default TopNav;
