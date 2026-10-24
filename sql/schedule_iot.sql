-- Ejecutar con el administrador, después de migrar y verificar la aplicación.
-- Crear previamente en Vault puentes_iot_url (URL HTTPS /internal/iot/pull)
-- y puentes_cron_secret (el mismo CRON_SECRET privado que usa Vercel).
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;
DO $$
DECLARE job bigint;
BEGIN
  FOR job IN SELECT jobid FROM cron.job WHERE jobname='puentes-iot-60s' LOOP
    PERFORM cron.unschedule(job);
  END LOOP;
END $$;
SELECT cron.schedule('puentes-iot-60s','* * * * *', $job$
SELECT net.http_post(
    url := (SELECT decrypted_secret FROM vault.decrypted_secrets WHERE name='puentes_iot_url'),
    headers := jsonb_build_object('Content-Type','application/json','Authorization','Bearer '||(SELECT decrypted_secret FROM vault.decrypted_secrets WHERE name='puentes_cron_secret')),
    body := '{}'::jsonb,
    timeout_milliseconds := 55000
);
$job$);
