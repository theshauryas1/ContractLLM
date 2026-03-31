create table if not exists trace_runs (
    id serial primary key,
    trace_id varchar(255) not null,
    prompt_version varchar(255) not null,
    input_payload jsonb not null,
    results jsonb not null,
    created_at timestamptz default now() not null
);
