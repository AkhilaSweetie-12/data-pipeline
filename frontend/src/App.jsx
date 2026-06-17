import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom'
import {
  AppBar, Toolbar, Typography, Box, Drawer, List, ListItemButton,
  ListItemIcon, ListItemText, Container, Chip, Button, Stack,
} from '@mui/material'
import DashboardIcon from '@mui/icons-material/Dashboard'
import PeopleIcon from '@mui/icons-material/People'
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart'
import HistoryIcon from '@mui/icons-material/History'
import LogoutIcon from '@mui/icons-material/Logout'
import Dashboard from './pages/Dashboard.jsx'
import Customers from './pages/Customers.jsx'
import Orders from './pages/Orders.jsx'
import Audit from './pages/Audit.jsx'
import Login from './pages/Login.jsx'
import { useAuth } from './auth'

const drawerWidth = 240

function RequireAuth({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return children
}

function Shell() {
  const location = useLocation()
  const { user, signOut, isAdmin } = useAuth()

  const navItems = [
    { label: 'Dashboard', path: '/', icon: <DashboardIcon /> },
    { label: 'Customers', path: '/customers', icon: <PeopleIcon /> },
    { label: 'Orders', path: '/orders', icon: <ShoppingCartIcon /> },
    ...(isAdmin ? [{ label: 'Audit Log', path: '/audit', icon: <HistoryIcon /> }] : []),
  ]

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Retail DataSecOps Platform
          </Typography>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <Chip label={`${user.username} · ${user.role}`} color="default"
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: '#fff' }} />
            <Button color="inherit" startIcon={<LogoutIcon />} onClick={signOut}>Logout</Button>
          </Stack>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {navItems.map((item) => (
              <ListItemButton
                key={item.path}
                component={Link}
                to={item.path}
                selected={location.pathname === item.path}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            ))}
          </List>
        </Box>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Container maxWidth="lg">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/audit" element={<Audit />} />
          </Routes>
        </Container>
      </Box>
    </Box>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={<RequireAuth><Shell /></RequireAuth>} />
    </Routes>
  )
}
