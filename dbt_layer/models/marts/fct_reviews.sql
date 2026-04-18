-- models/marts/fct_reviews.sql
with reviews as (select * from {{ ref('stg_reviews') }}),
     orders  as (select * from {{ ref('stg_orders') }}),
     custs   as (select * from {{ ref('stg_customers') }})

select
    r.review_id,
    r.order_id,
    r.review_score,
    r.review_comment_title,
    r.review_comment_message,
    r.review_created_at,
    r.review_answered_at,
    o.customer_id,
    c.customer_city,
    c.customer_state,
    o.order_status,
    o.purchased_at,
    o.delivered_at,
    datediff('day', o.purchased_at, r.review_created_at)  as days_to_review,
    datediff('day', o.purchased_at, o.delivered_at)        as delivery_days
from reviews r
join orders o on r.order_id   = o.order_id
join custs  c on o.customer_id = c.customer_id
