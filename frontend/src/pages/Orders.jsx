import { useEffect, useState } from 'react'
import {
  Box, Typography, Button, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Stack, Snackbar, Alert, MenuItem,
} from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import AddIcon from '@mui/icons-material/Add'
import { getOrders, createOrder, getCustomers } from '../api'
import { useAuth } from '../auth'

const today = new Date().toISOString().slice(0, 10)
const emptyForm = { customer_id: '', product_name: '', quantity: 1, amount: '', order_date: today }

export default function Orders() {
  const [rows, setRows] = useState([])
  const [customers, setCustomers] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [toast, setToast] = useState({ open: false, msg: '', severity: 'success' })
  const { canWrite } = useAuth()

  const notify = (msg, severity = 'success') => setToast({ open: true, msg, severity })
  const load = () => getOrders().then(setRows).catch(() => notify('Failed to load orders', 'error'))

  useEffect(() => {
    load()
    getCustomers().then(setCustomers).catch(() => {})
  }, [])

  const handleSubmit = async () => {
    try {
      await createOrder({
        ...form,
        customer_id: Number(form.customer_id),
        quantity: Number(form.quantity),
        amount: Number(form.amount),
      })
      notify('Order added')
      setOpen(false)
      setForm(emptyForm)
      load()
    } catch (e) {
      notify(e.response?.data?.detail || 'Operation failed', 'error')
    }
  }

  const columns = [
    { field: 'order_id', headerName: 'Order ID', width: 90 },
    { field: 'customer_id', headerName: 'Customer ID', width: 110 },
    { field: 'product_name', headerName: 'Product', flex: 1 },
    { field: 'quantity', headerName: 'Qty', width: 80 },
    { field: 'amount', headerName: 'Amount', width: 120,
      valueFormatter: (v) => `₹${Number(v).toLocaleString('en-IN')}` },
    { field: 'order_date', headerName: 'Order Date', width: 130 },
  ]

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4" fontWeight={700}>Orders</Typography>
        {canWrite && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpen(true)}>
            Add Order
          </Button>
        )}
      </Stack>

      <div style={{ height: 520, width: '100%' }}>
        <DataGrid
          rows={rows}
          columns={columns}
          getRowId={(r) => r.order_id}
          pageSizeOptions={[10, 25, 50]}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
        />
      </div>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Add Order</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField select label="Customer" value={form.customer_id}
              onChange={(e) => setForm({ ...form, customer_id: e.target.value })} required>
              {customers.map((c) => (
                <MenuItem key={c.customer_id} value={c.customer_id}>
                  {c.customer_id} - {c.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField label="Product Name" value={form.product_name}
              onChange={(e) => setForm({ ...form, product_name: e.target.value })} required />
            <TextField label="Quantity" type="number" value={form.quantity}
              onChange={(e) => setForm({ ...form, quantity: e.target.value })} required />
            <TextField label="Amount" type="number" value={form.amount}
              onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
            <TextField label="Order Date" type="date" value={form.order_date}
              InputLabelProps={{ shrink: true }}
              onChange={(e) => setForm({ ...form, order_date: e.target.value })} required />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSubmit}>Save</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={toast.open} autoHideDuration={4000}
        onClose={() => setToast({ ...toast, open: false })}>
        <Alert severity={toast.severity}>{toast.msg}</Alert>
      </Snackbar>
    </Box>
  )
}
