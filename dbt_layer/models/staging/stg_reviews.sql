-- models/staging/stg_reviews.sql
with source as (
    select * from read_parquet('{{ env_var("DATA_RAW_PATH", "data/raw") }}/olist_order_reviews_dataset.parquet')
),
renamed as (
    select
        review_id,
        order_id,
        cast(review_score as integer)                   as review_score,
        review_comment_title,
        review_comment_message,
        cast(review_creation_date as timestamp)         as review_created_at,
        cast(review_answer_timestamp as timestamp)      as review_answered_at
    from source
)
select * from renamed
