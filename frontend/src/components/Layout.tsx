import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const location = useLocation()

  const navLinks = [
    { href: '/', label: 'Files' },
    { href: '/trash', label: 'Trash' },
    ...(user?.is_admin ? [{ href: '/admin', label: 'Admin' }] : []),
  ]

  return (
    <div className='min-h-screen flex flex-col'>
      <header className='glass border-b border-white/5 sticky top-0 z-50'>
        <div className='max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between'>
          <div className='flex items-center gap-8'>
            <Link to='/' className='flex items-center gap-2.5 group'>
              <div className='w-8 h-8 rounded-xl bg-gradient-to-br from-vault-amber to-amber-500 flex items-center justify-center text-sm font-bold text-vault-bg shadow-lg shadow-vault-amber/20 group-hover:shadow-vault-amber/30 transition-shadow'>
                T
              </div>
              <span className='text-lg font-semibold tracking-tight'>
                <span className='gradient-text'>Trove</span>
              </span>
            </Link>
            <nav className='hidden sm:flex items-center gap-1'>
              {navLinks.map(link => (
                <Link
                  key={link.href}
                  to={link.href}
                  className={'nav-link' + (location.pathname === link.href ? ' active' : '')}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className='flex items-center gap-3'>
            {user && (
              <>
                <span className='text-sm text-vault-muted hidden sm:block'>
                  <span className='font-mono text-xs bg-white/5 px-2 py-1 rounded-lg'>@{user.username}</span>
                </span>
                <button
                  onClick={logout}
                  className='text-sm text-vault-muted hover:text-red-400 transition-colors px-3 py-1.5 rounded-lg hover:bg-red-500/5'
                >
                  Logout
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      <main className='flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 sm:py-8 animate-fade-in'>
        {children}
      </main>
    </div>
  )
}
