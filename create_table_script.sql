-- Table: public.registration_test

-- DROP TABLE IF EXISTS public.registration_test;

CREATE TABLE IF NOT EXISTS public.registration_test
(
    school_name character varying COLLATE pg_catalog."default" NOT NULL,
    student_name character varying COLLATE pg_catalog."default" NOT NULL,
    email character varying COLLATE pg_catalog."default",
    phone character varying COLLATE pg_catalog."default",
    jersey_number character varying COLLATE pg_catalog."default"
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.registration_test
    OWNER to admin;
    
