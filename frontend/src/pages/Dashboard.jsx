import { useEffect, useState } from 'react'
import {
  Grid, Card, CardContent, Typography, Box, Paper, Alert, CircularProgress,
} from '@mui/material'
import AttachMoneyIcon from '@mui/icons-material/AttachMoney'
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong'
import PeopleIcon from '@mui/icons-material/People'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'
import { getDashboardMetrics } from '../api'

function StatCard({ title, value, icon, color }) {
  return (
    <Card elevation={3}>
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box sx={{ bgcolor: color, color: '#fff', p: 1.5, borderRadius: 2, display: 'flex' }}>
          {icon}
        </Box>
        <Box>
          <Typography variant="body2" color="text.secondary">{title}</Typography>
          <Typography variant="h5" fontWeight={700}>{value}</Typography>
        </Box>
      </CardContent>
    </Card>
  )
}

const currency = (n) => `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboardMetrics()
      .then(setMetrics)
      .catch(() => setError('Failed to load dashboard metrics. Is the API running?'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Box sx={{ textAlign: 'center', mt: 6 }}><CircularProgress /></Box>
  if (error) return <Alert severity="error">{error}</Alert>

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight={700}>Dashboard</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <StatCard title="Total Revenue" value={currency(metrics.total_revenue)}
            icon={<AttachMoneyIcon />} color="#1565c0" />
        </Grid>
        <Grid item xs={12} md={4}>
          <StatCard title="Total Orders" value={metrics.total_orders}
            icon={<ReceiptLongIcon />} color="#00897b" />
        </Grid>
        <Grid item xs={12} md={4}>
          <StatCard title="Total Customers" value={metrics.total_customers}
            icon={<PeopleIcon />} color="#6a1b9a" />
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 360 }}>
            <Typography variant="h6" gutterBottom>Revenue by City</Typography>
            <ResponsiveContainer width="100%" height="90%">
              <BarChart data={metrics.revenue_by_city}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="city" />
                <YAxis />
                <Tooltip formatter={(v) => currency(v)} />
                <Bar dataKey="revenue" fill="#1565c0" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 360 }}>
            <Typography variant="h6" gutterBottom>Top Customers</Typography>
            <ResponsiveContainer width="100%" height="90%">
              <BarChart data={metrics.top_customers} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="name" width={110} />
                <Tooltip formatter={(v) => currency(v)} />
                <Bar dataKey="total_spent" fill="#00897b" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
