-- models/staging/stg_order_items.sql
with source as (
    select * from read_parquet('{{ env_var("DATA_RAW_PATH", "data/raw") }}/olist_order_items_dataset.parquet')
),
renamed as (
    select
        order_id,
        order_item_id,
        product_id,
        seller_id,
        cast(shipping_limit_date as timestamp) as shipping_limit_at,
        cast(price as double)                  as price,
        cast(freight_value as double)          as freight_value
    from source
)
select * from renamed
