-- Schema gerado automaticamente por src/q2_generate_schema.py
-- Tipos inferidos a partir dos valores observados em cada CSV (ver logica em ColumnProfile).
-- Sem PRIMARY KEY / FOREIGN KEY: nao foram pedidos pela tarefa, apenas a criacao das tabelas.

CREATE TABLE "addresses" (
    "id" BIGINT NOT NULL,
    "customer_id" BIGINT NOT NULL,
    "address_type" TEXT NOT NULL,
    "postal_code" TEXT NOT NULL,
    "street" TEXT NOT NULL,
    "number" BIGINT NOT NULL,
    "complement" TEXT,
    "district" TEXT NOT NULL,
    "city" TEXT NOT NULL,
    "state" TEXT NOT NULL,
    "country" TEXT NOT NULL,
    "is_primary" BOOLEAN NOT NULL
);

CREATE TABLE "attributes" (
    "id" BIGINT NOT NULL,
    "name" TEXT NOT NULL,
    "data_type" TEXT NOT NULL
);

CREATE TABLE "brands" (
    "id" BIGINT NOT NULL,
    "name" TEXT NOT NULL,
    "country" TEXT,
    "is_active" BOOLEAN NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "categories" (
    "id" BIGINT NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "parent_category_id" BIGINT,
    "is_active" BOOLEAN NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "customers" (
    "id" BIGINT NOT NULL,
    "person_type" TEXT NOT NULL,
    "legal_name" TEXT NOT NULL,
    "trade_name" TEXT,
    "tax_id" BIGINT NOT NULL,
    "state_registration" TEXT,
    "email" TEXT,
    "phone" TEXT,
    "is_active" BOOLEAN NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "employees" (
    "id" BIGINT NOT NULL,
    "full_name" TEXT NOT NULL,
    "cpf" BIGINT NOT NULL,
    "email" TEXT NOT NULL,
    "role" TEXT NOT NULL,
    "primary_location_id" BIGINT NOT NULL,
    "hire_date" DATE NOT NULL,
    "termination_date" DATE,
    "is_active" BOOLEAN NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "fiscal_invoices" (
    "id" BIGINT NOT NULL,
    "order_id" BIGINT NOT NULL,
    "nfe_number" TEXT NOT NULL,
    "nfe_access_key" NUMERIC NOT NULL,
    "series" BIGINT NOT NULL,
    "issued_at" TIMESTAMP NOT NULL,
    "status" TEXT NOT NULL,
    "total_amount" NUMERIC NOT NULL,
    "xml_storage_uri" TEXT NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "goods_receipt_items" (
    "id" BIGINT NOT NULL,
    "goods_receipt_id" BIGINT NOT NULL,
    "purchase_order_item_id" BIGINT NOT NULL,
    "quantity_received" NUMERIC NOT NULL
);

CREATE TABLE "goods_receipts" (
    "id" BIGINT NOT NULL,
    "purchase_order_id" BIGINT NOT NULL,
    "received_by_employee_id" BIGINT NOT NULL,
    "received_at" TIMESTAMP NOT NULL,
    "notes" TEXT,
    "created_at" TIMESTAMP NOT NULL
);

CREATE TABLE "locations" (
    "id" BIGINT NOT NULL,
    "name" TEXT NOT NULL,
    "location_type" TEXT NOT NULL,
    "postal_code" TEXT NOT NULL,
    "street" TEXT NOT NULL,
    "number" BIGINT NOT NULL,
    "complement" TEXT,
    "district" TEXT NOT NULL,
    "city" TEXT NOT NULL,
    "state" TEXT NOT NULL,
    "country" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "order_items" (
    "id" BIGINT NOT NULL,
    "order_id" BIGINT NOT NULL,
    "product_variant_id" BIGINT NOT NULL,
    "quantity" BIGINT NOT NULL,
    "unit_price" NUMERIC NOT NULL,
    "icms_rate" NUMERIC NOT NULL,
    "ipi_rate" NUMERIC NOT NULL,
    "line_total" NUMERIC NOT NULL
);

CREATE TABLE "orders" (
    "id" BIGINT NOT NULL,
    "order_number" TEXT NOT NULL,
    "channel" TEXT NOT NULL,
    "customer_id" BIGINT NOT NULL,
    "salesperson_id" BIGINT,
    "location_id" BIGINT NOT NULL,
    "status" TEXT NOT NULL,
    "subtotal" NUMERIC NOT NULL,
    "discount_amount" NUMERIC NOT NULL,
    "total" NUMERIC NOT NULL,
    "placed_at" TIMESTAMP NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "payments" (
    "id" BIGINT NOT NULL,
    "order_id" BIGINT NOT NULL,
    "method" TEXT NOT NULL,
    "installments" BIGINT NOT NULL,
    "amount" NUMERIC NOT NULL,
    "status" TEXT NOT NULL,
    "paid_at" TIMESTAMP,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "product_suppliers" (
    "product_variant_id" BIGINT NOT NULL,
    "supplier_id" BIGINT NOT NULL,
    "supplier_sku" TEXT,
    "last_quoted_cost" NUMERIC NOT NULL,
    "lead_time_days" BIGINT NOT NULL,
    "is_preferred" BOOLEAN NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "product_variants" (
    "id" BIGINT NOT NULL,
    "product_id" BIGINT NOT NULL,
    "sku" TEXT NOT NULL,
    "barcode_ean" BIGINT,
    "sale_price" NUMERIC NOT NULL,
    "cost_price" NUMERIC NOT NULL,
    "weight_kg" NUMERIC NOT NULL,
    "icms_rate" NUMERIC NOT NULL,
    "ipi_rate" NUMERIC NOT NULL,
    "is_active" BOOLEAN NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "products" (
    "id" BIGINT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "brand_id" BIGINT NOT NULL,
    "category_id" BIGINT NOT NULL,
    "ncm_code" BIGINT NOT NULL,
    "unit_of_measure" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "purchase_order_items" (
    "id" BIGINT NOT NULL,
    "purchase_order_id" BIGINT NOT NULL,
    "product_variant_id" BIGINT NOT NULL,
    "quantity_ordered" BIGINT NOT NULL,
    "unit_cost" NUMERIC NOT NULL,
    "line_total" NUMERIC NOT NULL
);

CREATE TABLE "purchase_orders" (
    "id" BIGINT NOT NULL,
    "po_number" TEXT NOT NULL,
    "supplier_id" BIGINT NOT NULL,
    "buyer_id" BIGINT NOT NULL,
    "destination_location_id" BIGINT NOT NULL,
    "status" TEXT NOT NULL,
    "currency" TEXT NOT NULL,
    "subtotal" NUMERIC NOT NULL,
    "total" NUMERIC NOT NULL,
    "placed_at" TIMESTAMP NOT NULL,
    "expected_delivery_at" DATE,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "return_items" (
    "id" BIGINT NOT NULL,
    "return_id" BIGINT NOT NULL,
    "order_item_id" BIGINT NOT NULL,
    "quantity" NUMERIC NOT NULL,
    "action" TEXT NOT NULL,
    "exchange_variant_id" BIGINT,
    "unit_refund_amount" NUMERIC NOT NULL
);

CREATE TABLE "returns" (
    "id" BIGINT NOT NULL,
    "return_number" TEXT NOT NULL,
    "order_id" BIGINT NOT NULL,
    "customer_id" BIGINT NOT NULL,
    "received_at_location_id" BIGINT NOT NULL,
    "status" TEXT NOT NULL,
    "reason" TEXT,
    "total_refund_amount" NUMERIC NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "stock_levels" (
    "product_variant_id" BIGINT NOT NULL,
    "location_id" BIGINT NOT NULL,
    "quantity_on_hand" NUMERIC NOT NULL,
    "reorder_point" TEXT,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "stock_movements" (
    "id" BIGINT NOT NULL,
    "product_variant_id" BIGINT NOT NULL,
    "location_id" BIGINT NOT NULL,
    "movement_type" TEXT NOT NULL,
    "quantity" NUMERIC NOT NULL,
    "reference_table" TEXT,
    "reference_id" BIGINT,
    "employee_id" BIGINT,
    "notes" TEXT,
    "occurred_at" TIMESTAMP NOT NULL,
    "created_at" TIMESTAMP NOT NULL
);

CREATE TABLE "suppliers" (
    "id" BIGINT NOT NULL,
    "legal_name" TEXT NOT NULL,
    "trade_name" TEXT,
    "country" TEXT NOT NULL,
    "tax_id" TEXT NOT NULL,
    "tax_id_type" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "phone" BIGINT NOT NULL,
    "contact_name" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);

CREATE TABLE "variant_attribute_values" (
    "product_variant_id" BIGINT NOT NULL,
    "attribute_id" BIGINT NOT NULL,
    "value" TEXT NOT NULL
);
