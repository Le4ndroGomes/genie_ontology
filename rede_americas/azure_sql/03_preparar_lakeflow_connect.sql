/* Prepara o banco rede_americas_ontologia para o Lakeflow Connect (rodar depois de 01_ddl, 02_dados e
   lakeflow_utility_script.sql). O LOGIN dbx_ingest é criado antes por 00_login_master.sql
   (no master); aqui ele ganha um USER neste banco. Change tracking com retenção de 7 dias, porque o gateway fica
   parado entre as demos. */
IF USER_ID('dbx_ingest') IS NULL CREATE USER dbx_ingest FOR LOGIN dbx_ingest;
GO
EXEC dbo.lakeflowSetupChangeTracking
     @Tables = 'SCHEMAS:cadastro,assistencial,faturamento,relacionamento',
     @User = 'dbx_ingest', @Retention = '7 DAYS', @Mode = 'INSTALL', @CreateDdlSupportingObjects = 1;
GO
EXEC dbo.lakeflowFixPermissions @User = 'dbx_ingest',
     @Tables = 'SCHEMAS:cadastro,assistencial,faturamento,relacionamento';
GO
/* conferência: deve listar as 22 tabelas */
SELECT s.name AS esquema, t.name AS tabela
FROM sys.change_tracking_tables ct JOIN sys.tables t ON t.object_id = ct.object_id
JOIN sys.schemas s ON s.schema_id = t.schema_id ORDER BY 1, 2;
