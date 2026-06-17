import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({ baseURL, headers: { 'Content-Type': 'application/json' } })

// Attach JWT from localStorage to every request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401, clear session and force re-login.
api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

// Auth
export const login = async (username, password) => {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  const { data } = await api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}
export const getAuditLogs = () => api.get('/auth/audit').then((r) => r.data)

// Customers
export const getCustomers = () => api.get('/customers').then((r) => r.data)
export const createCustomer = (data) => api.post('/customers', data).then((r) => r.data)
export const updateCustomer = (id, data) => api.put(`/customers/${id}`, data).then((r) => r.data)

// Orders
export const getOrders = () => api.get('/orders').then((r) => r.data)
export const createOrder = (data) => api.post('/orders', data).then((r) => r.data)

// Dashboard
export const getDashboardMetrics = () => api.get('/dashboard/metrics').then((r) => r.data)

export default api
