-- Table: public.registration

-- DROP TABLE IF EXISTS public.registration;

CREATE TABLE IF NOT EXISTS public.registration
(
    pid character varying collate pg_catalog."default" not null,
	school_name character varying COLLATE pg_catalog."default" NOT NULL,
	team_id character varying collate pg_catalog."default" not null, 
    student_name character varying COLLATE pg_catalog."default" NOT NULL,
    email character varying COLLATE pg_catalog."default",
    phone character varying COLLATE pg_catalog."default",
    jersey_number character varying COLLATE pg_catalog."default",
	update_time timestamp without time zone,
	constraint registration_pkey primary key (pid)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.registration
    OWNER to admin;