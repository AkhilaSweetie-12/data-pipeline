import { useEffect, useState } from 'react'
import { Box, Typography, Alert } from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import { getAuditLogs } from '../api'

export default function Audit() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    getAuditLogs().then(setRows).catch(() => setError('Failed to load audit logs (admin only).'))
  }, [])

  const columns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'created_at', headerName: 'Timestamp', width: 200 },
    { field: 'username', headerName: 'User', width: 120 },
    { field: 'role', headerName: 'Role', width: 120 },
    { field: 'action', headerName: 'Action', width: 100 },
    { field: 'resource', headerName: 'Resource', width: 120 },
    { field: 'detail', headerName: 'Detail', flex: 1 },
    { field: 'status_code', headerName: 'Status', width: 90 },
  ]

  if (error) return <Alert severity="error">{error}</Alert>

  return (
    <Box>
      <Typography variant="h4" fontWeight={700} mb={2}>Audit Log</Typography>
      <div style={{ height: 560, width: '100%' }}>
        <DataGrid rows={rows} columns={columns} getRowId={(r) => r.id}
          pageSizeOptions={[25, 50, 100]}
          initialState={{ pagination: { paginationModel: { pageSize: 25 } } }} />
      </div>
    </Box>
  )
}
