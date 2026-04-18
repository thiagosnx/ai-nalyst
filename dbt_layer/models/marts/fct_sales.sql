-- models/marts/fct_sales.sql
with orders as (select * from {{ ref('stg_orders') }}),
     items  as (select * from {{ ref('stg_order_items') }}),
     prods  as (select * from {{ ref('stg_products') }}),
     custs  as (select * from {{ ref('stg_customers') }})

select
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    o.order_status,
    o.purchased_at,
    o.approved_at,
    o.delivered_carrier_at,
    o.delivered_at,
    o.estimated_delivery_at,
    i.order_item_id,
    i.product_id,
    p.product_category_name,
    i.price,
    i.freight_value,
    (i.price + i.freight_value)                          as total_value,
    i.seller_id,
    date_trunc('month', o.purchased_at)                  as purchased_month,
    date_trunc('year', o.purchased_at)                   as purchased_year,
    datediff('day', o.purchased_at, o.delivered_at)      as delivery_days
from orders o
join items  i on o.order_id   = i.order_id
join prods  p on i.product_id = p.product_id
join custs  c on o.customer_id = c.customer_id
