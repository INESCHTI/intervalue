import { type ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  LayoutDashboard,
  Briefcase,
  CandlestickChart,
  Sparkles,
  LogOut,
  ShieldCheck,
} from 'lucide-react'
import { getMeshHealth } from '../api/client'
import { useAuth } from '../auth/useAuth'

const NAV = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { to: '/market', label: 'Markets', icon: CandlestickChart },
  { to: '/chat', label: 'AI Assistant', icon: Sparkles },
]

export default function Layout({ children }: { children: ReactNode }) {
  const { username, logout } = useAuth()
  const mesh = useQuery({ queryKey: ['mesh-health'], queryFn: getMeshHealth, refetchInterval: 10_000 })

  const healthyCount = mesh.data?.services.filter(service => service.status === 'ok').length ?? 0
  const totalCount = mesh.data?.services.length ?? 0
  const meshStatus = mesh.isError ? 'down' : (mesh.data?.status ?? 'degraded')

  return (
    <div className="app-shell">
      <nav className="sidebar">
        <div className="brand-block">
          <img className="brand-mark brand-mark-image" src="/brand/laruche-mark.png" alt="LaRuche" />
          <div>
            <h1 className="brand-name">LaRuche</h1>
            <p className="brand-caption">Private Wealth Intelligence</p>
          </div>
        </div>

        <div className="nav-list">
          <p className="nav-kicker">Workspace</p>
          {NAV.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `nav-item ${isActive ? 'nav-item-active' : ''}`
              }
            >
              <span className="nav-icon"><item.icon className="h-4 w-4" /></span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="mesh-mini-card">
            <div>
              <span className={`status-dot ${meshStatus === 'ok' ? 'status-dot-ready' : 'status-dot-warn'}`} />
              <strong>Agent Mesh</strong>
            </div>
            <span>{totalCount ? `${healthyCount}/${totalCount}` : mesh.isError ? 'offline' : 'checking'}</span>
          </div>

          <div className="security-chip">
            <ShieldCheck className="h-3.5 w-3.5" />
            Secure advisory session
          </div>
          <div className="user-row">
            <div className="user-avatar">
              {username?.[0]?.toUpperCase() ?? 'U'}
            </div>
            <div className="min-w-0 flex-1">
              <p className="user-name">{username ?? 'Advisor'}</p>
              <p className="user-role">Advisor access</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="signout-button"
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign out
          </button>
        </div>
      </nav>

      <main className="main-canvas">
        <div className="ambient ambient-one" />
        <div className="ambient ambient-two" />
        <div className="content-frame">{children}</div>
      </main>

    </div>
  )
}
