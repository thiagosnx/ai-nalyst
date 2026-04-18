-- models/staging/stg_sellers.sql
with source as (
    select * from read_parquet('{{ env_var("DATA_RAW_PATH", "data/raw") }}/olist_sellers_dataset.parquet')
),
renamed as (
    select
        seller_id,
        cast(seller_zip_code_prefix as varchar) as seller_zip_code_prefix,
        seller_city,
        seller_state
    from source
)
select * from renamed
