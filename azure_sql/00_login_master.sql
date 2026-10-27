/* Rodar no banco MASTER do servidor, como administrador. Cria o login de ingestão do Lakeflow Connect.
   O gateway entra primeiro em master; por isso o login precisa de um USER também aqui, não só no banco da demo.
   Troque a senha antes de rodar e guarde-a num cofre (ela vai na conexão do Unity Catalog). */
IF NOT EXISTS (SELECT 1 FROM sys.sql_logins WHERE name = 'dbx_ingest')
    CREATE LOGIN dbx_ingest WITH PASSWORD = '<troque-por-uma-senha-forte>';
IF USER_ID('dbx_ingest') IS NULL CREATE USER dbx_ingest FOR LOGIN dbx_ingest;
