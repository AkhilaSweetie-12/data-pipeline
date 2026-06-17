/* =====================================================================
   Retail DataSecOps - Sample / test data
   Includes deliberately "dirty" rows to exercise the Silver-layer
   data-quality and quarantine logic.
   ===================================================================== */

SET IDENTITY_INSERT dbo.customers ON;
INSERT INTO dbo.customers (customer_id, name, email, phone, city) VALUES
 (1, 'Alice Johnson', 'alice@example.com',   '9000000001', 'Chennai'),
 (2, 'Bob Smith',     'bob@example.com',     '9000000002', 'Mumbai'),
 (3, 'Carol White',   'carol@example.com',   '9000000003', 'Bangalore'),
 (4, 'David Lee',     'david@example.com',   '9000000004', 'Delhi'),
 (5, 'Eva Brown',     'eva@example.com',     '9000000005', 'Hyderabad'),
 (6, 'Frank Green',   'frank-invalid-email', '9000000006', 'Pune'),     -- invalid email -> quarantine
 (7, 'Grace Hall',    NULL,                  '9000000007', 'Chennai');  -- null email -> quarantine
SET IDENTITY_INSERT dbo.customers OFF;
GO

SET IDENTITY_INSERT dbo.orders ON;
INSERT INTO dbo.orders (order_id, customer_id, product_name, quantity, amount, order_date) VALUES
 (1, 1, 'Laptop',     1, 1200.00, '2024-05-01'),
 (2, 1, 'Mouse',      2,   40.00, '2024-05-03'),
 (3, 2, 'Phone',      1,  800.00, '2024-05-05'),
 (4, 3, 'Monitor',    2,  600.00, '2024-05-06'),
 (5, 3, 'Keyboard',   1,   75.00, '2024-05-07'),
 (6, 4, 'Tablet',     1,  450.00, '2024-05-09'),
 (7, 5, 'Headphones', 3,  300.00, '2024-05-10'),
 (8, 2, 'Laptop',     1, 1100.00, '2024-05-12');
SET IDENTITY_INSERT dbo.orders OFF;
GO
