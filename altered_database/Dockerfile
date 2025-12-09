FROM postgres:17-alpine

# prod 
ENV POSTGRES_PASSWORD=kochamy_bazy_danych
ENV POSTGRES_USER=kbd
ENV POSTGRES_DB=pdb_demo

COPY ddl.sql /docker-entrypoint-initdb.d/og_schema.sql

EXPOSE 5432
