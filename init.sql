
CREATE TABLE IF NOT EXISTS public."core_user" (
    id SERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMPTZ NULL,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    identification VARCHAR(30) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS public."core_user_groups" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES public."core_user"(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS public."core_user_user_permissions" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES public."core_user"(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL
);

INSERT INTO public."core_user" (password, identification, full_name, is_staff, is_superuser, is_active)
VALUES (
    '${DEFAULT_PASSWORD_HASH}',
    '${DEFAULT_ID}',
    '${DEFAULT_NAME}',
    TRUE,
    TRUE,
    TRUE
)
ON CONFLICT (identification) DO NOTHING;
