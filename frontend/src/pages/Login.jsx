import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Paper, TextField, Button, Typography, Alert, Stack, Chip,
} from '@mui/material'
import LockIcon from '@mui/icons-material/Lock'
import { useAuth } from '../auth'

export default function Login() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await signIn(username, password)
      navigate('/')
    } catch {
      setError('Invalid username or password')
    } finally {
      setLoading(false)
    }
  }

  const quickFill = (u, p) => { setUsername(u); setPassword(p) }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      bgcolor: 'background.default' }}>
      <Paper elevation={4} sx={{ p: 4, width: 380 }}>
        <Stack alignItems="center" spacing={1} mb={2}>
          <LockIcon color="primary" fontSize="large" />
          <Typography variant="h5" fontWeight={700}>Retail DataSecOps</Typography>
          <Typography variant="body2" color="text.secondary">Sign in to continue</Typography>
        </Stack>
        <form onSubmit={submit}>
          <Stack spacing={2}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField label="Username" value={username} autoFocus
              onChange={(e) => setUsername(e.target.value)} required />
            <TextField label="Password" type="password" value={password}
              onChange={(e) => setPassword(e.target.value)} required />
            <Button type="submit" variant="contained" disabled={loading} size="large">
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </Stack>
        </form>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
          DEV demo accounts (click to fill):
        </Typography>
        <Stack direction="row" spacing={1} mt={1} flexWrap="wrap" useFlexGap>
          <Chip size="small" label="admin" onClick={() => quickFill('admin', 'admin123')} />
          <Chip size="small" label="engineer" onClick={() => quickFill('engineer', 'engineer123')} />
          <Chip size="small" label="analyst" onClick={() => quickFill('analyst', 'analyst123')} />
        </Stack>
      </Paper>
    </Box>
  )
}
