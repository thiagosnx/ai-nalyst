-- models/staging/stg_customers.sql
with source as (
    select * from read_parquet('{{ env_var("DATA_RAW_PATH", "data/raw") }}/olist_customers_dataset.parquet')
),
renamed as (
    select
        customer_id,
        customer_unique_id,
        cast(customer_zip_code_prefix as varchar) as customer_zip_code_prefix,
        customer_city,
        customer_state
    from source
)
select * from renamed
