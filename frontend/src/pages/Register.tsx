import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Register() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(username, password)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='min-h-screen flex items-center justify-center p-4 relative overflow-hidden'>
      <div className='absolute inset-0' style={{
        background: 'radial-gradient(ellipse at 30% 20%, rgba(201, 154, 62, 0.06) 0%, transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(201, 154, 62, 0.04) 0%, transparent 50%)'
      }} />
      <div className='relative w-full max-w-sm'>
        <div className='text-center mb-8 animate-slide-up'>
          <div className='w-14 h-14 rounded-2xl bg-gradient-to-br from-vault-amber to-amber-500 flex items-center justify-center text-2xl font-bold text-vault-bg mx-auto mb-4 shadow-xl shadow-vault-amber/20'>T</div>
          <h1 className='text-2xl font-bold gradient-text'>Trove</h1>
          <p className='text-sm text-vault-muted mt-1'>Create your vault</p>
        </div>
        <form onSubmit={handleSubmit} className='glass-card p-8 space-y-4 animate-slide-up'>
          <h2 className='text-lg font-semibold mb-1'>Create account</h2>
          {error && <div className='text-sm text-red-400 bg-red-500/10 rounded-lg px-3 py-2'>{error}</div>}
          <div>
            <input className='input-field' placeholder='Username' value={username} onChange={e => setUsername(e.target.value)} required />
          </div>
          <div>
            <input className='input-field' type='password' placeholder='Password' value={password} onChange={e => setPassword(e.target.value)} required minLength={6} />
          </div>
          <button type='submit' disabled={loading} className='btn-primary w-full !py-3'>
            {loading ? 'Creating...' : 'Create account'}
          </button>
          <p className='text-sm text-center text-vault-muted'>
            Already have one?{' '}
            <Link to='/login' className='text-vault-amber hover:text-vault-amber/80 transition-colors'>Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
