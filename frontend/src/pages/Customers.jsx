import { useEffect, useState } from 'react'
import {
  Box, Typography, Button, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Stack, Snackbar, Alert,
} from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import AddIcon from '@mui/icons-material/Add'
import { getCustomers, createCustomer, updateCustomer } from '../api'
import { useAuth } from '../auth'

const emptyForm = { name: '', email: '', phone: '', city: '' }

export default function Customers() {
  const [rows, setRows] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [editId, setEditId] = useState(null)
  const [toast, setToast] = useState({ open: false, msg: '', severity: 'success' })
  const { canWrite } = useAuth()

  const load = () => getCustomers().then(setRows).catch(() => notify('Failed to load customers', 'error'))
  useEffect(() => { load() }, [])

  const notify = (msg, severity = 'success') => setToast({ open: true, msg, severity })

  const handleOpen = (row = null) => {
    if (row) {
      setEditId(row.customer_id)
      setForm({ name: row.name, email: row.email, phone: row.phone || '', city: row.city || '' })
    } else {
      setEditId(null)
      setForm(emptyForm)
    }
    setOpen(true)
  }

  const handleSubmit = async () => {
    try {
      if (editId) {
        await updateCustomer(editId, form)
        notify('Customer updated')
      } else {
        await createCustomer(form)
        notify('Customer added')
      }
      setOpen(false)
      load()
    } catch (e) {
      notify(e.response?.data?.detail || 'Operation failed', 'error')
    }
  }

  const columns = [
    { field: 'customer_id', headerName: 'ID', width: 80 },
    { field: 'name', headerName: 'Name', flex: 1 },
    { field: 'email', headerName: 'Email', flex: 1 },
    { field: 'phone', headerName: 'Phone', width: 150 },
    { field: 'city', headerName: 'City', width: 130 },
    ...(canWrite ? [{
      field: 'actions', headerName: 'Actions', width: 110, sortable: false,
      renderCell: (params) => (
        <Button size="small" onClick={() => handleOpen(params.row)}>Edit</Button>
      ),
    }] : []),
  ]

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4" fontWeight={700}>Customers</Typography>
        {canWrite && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpen()}>
            Add Customer
          </Button>
        )}
      </Stack>

      <div style={{ height: 520, width: '100%' }}>
        <DataGrid
          rows={rows}
          columns={columns}
          getRowId={(r) => r.customer_id}
          pageSizeOptions={[10, 25, 50]}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
        />
      </div>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editId ? 'Edit Customer' : 'Add Customer'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField label="Name" value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            <TextField label="Email" type="email" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} required />
            <TextField label="Phone" value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            <TextField label="City" value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })} />
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
