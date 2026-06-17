/* =====================================================================
   Retail DataSecOps - Azure SQL Database schema
   Source (OLTP) system feeding the Databricks Medallion pipeline.
   ===================================================================== */

IF OBJECT_ID('dbo.orders', 'U') IS NOT NULL DROP TABLE dbo.orders;
IF OBJECT_ID('dbo.customers', 'U') IS NOT NULL DROP TABLE dbo.customers;
GO

CREATE TABLE dbo.customers (
    customer_id   INT IDENTITY(1,1) NOT NULL,
    name          NVARCHAR(200)     NOT NULL,
    -- email is nullable on purpose: Bronze ingests raw data as-is and the
    -- Silver layer quarantines null/invalid emails (DataSecOps shift-left DQ).
    email         NVARCHAR(255)     NULL,
    phone         NVARCHAR(30)      NULL,
    city          NVARCHAR(120)     NULL,
    created_at    DATETIME2         NOT NULL CONSTRAINT DF_customers_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_customers PRIMARY KEY (customer_id)
);
GO

CREATE TABLE dbo.orders (
    order_id      INT IDENTITY(1,1) NOT NULL,
    customer_id   INT               NOT NULL,
    product_name  NVARCHAR(200)     NOT NULL,
    quantity      INT               NOT NULL,
    amount        DECIMAL(12,2)     NOT NULL,
    order_date    DATE              NOT NULL,
    created_at    DATETIME2         NOT NULL CONSTRAINT DF_orders_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_orders PRIMARY KEY (order_id),
    CONSTRAINT FK_orders_customers FOREIGN KEY (customer_id)
        REFERENCES dbo.customers (customer_id),
    CONSTRAINT CK_orders_quantity CHECK (quantity > 0),
    CONSTRAINT CK_orders_amount CHECK (amount > 0)
);
GO

CREATE INDEX IX_orders_customer_id ON dbo.orders (customer_id);
CREATE INDEX IX_orders_order_date ON dbo.orders (order_date);
GO
