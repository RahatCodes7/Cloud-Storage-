import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import ShareDownload from './pages/ShareDownload'
import Admin from './pages/Admin'
import Layout from './components/Layout'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()
  if (isLoading) return <div className='flex h-screen items-center justify-center'><div className='animate-spin w-8 h-8 border-2 border-vault-amber border-t-transparent rounded-full' /></div>
  if (!user) return <Navigate to='/login' replace />
  return <>{children}</>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  if (!user?.is_admin) return <Navigate to='/' replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path='/login' element={<Login />} />
      <Route path='/register' element={<Register />} />
      <Route path='/s/:token' element={<ShareDownload />} />
      <Route path='/' element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
      <Route path='/trash' element={<ProtectedRoute><Layout><Dashboard trashed /></Layout></ProtectedRoute>} />
      <Route path='/admin' element={<ProtectedRoute><AdminRoute><Layout><Admin /></Layout></AdminRoute></ProtectedRoute>} />
    </Routes>
  )
}
