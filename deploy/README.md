# Despliegue (Google Cloud e2-micro / Oracle Cloud Always Free)

> **Producción actual:** Google Cloud, VM `e2-micro` en `us-east1-b` (Ubuntu 24.04, 1 GB RAM
> + 2 GB swap, Gunicorn con 2 workers). Ver [Google Cloud](#google-cloud-e2-micro) abajo;
> los pasos de Oracle quedan como alternativa si algún día hay capacidad para una A1.

Arquitectura final:

```
Visitante ──HTTPS──▶ Cloudflare ──HTTPS (Origin Cert)──▶ nginx ──unix socket──▶ gunicorn ──▶ Django + SQLite
                                                           └── /media/ servido directo desde disco
                                                           (estáticos: WhiteNoise dentro de Django)
```

Estructura en el servidor:

```
/srv/blog/
├── app/            # git clone del repo (+ .env)
├── venv/           # entorno virtual
├── data/           # db.sqlite3
├── media/          # imágenes subidas
├── staticfiles/    # salida de collectstatic
└── backups/
```

---

## 1. Cuenta y VM en Oracle

1. Crea la cuenta en https://www.oracle.com/cloud/free/ y elige como **home region** una
   cercana (p. ej. Madrid o Frankfurt). No se puede cambiar después.
2. **Recomendado:** pasa la cuenta a *Pay As You Go*. Mientras uses solo recursos
   Always Free no te cobran nada, pero evita que Oracle reclame instancias "inactivas"
   (un blog con poco tráfico lo es). Crea también una alerta de presupuesto de 1 € en
   *Billing → Budgets* para estar tranquilo.
3. *Compute → Instances → Create instance*:
   - Image: **Ubuntu 24.04** (Canonical).
   - Shape: **VM.Standard.A1.Flex** (Ampere ARM), 1 OCPU y 6 GB de RAM es de sobra.
   - Networking: crea una VCN nueva con subnet pública y **asigna IP pública**.
   - SSH keys: sube tu clave pública (`~/.ssh/id_ed25519.pub`).
   - Si da error *Out of capacity*, prueba otro *Availability Domain* o reintenta más tarde.
4. Abre los puertos en la **Security List** de la subnet
   (*Networking → VCN → Security Lists → Default → Add Ingress Rules*):
   - Source `0.0.0.0/0`, TCP, destination port `80`
   - Source `0.0.0.0/0`, TCP, destination port `443`

## 2. Preparar el servidor

```bash
ssh ubuntu@IP_DEL_SERVIDOR
```

Las imágenes de Oracle traen iptables cerrando todo excepto SSH. Abre 80 y 443:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

Paquetes y usuario de la app:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-dev build-essential nginx git sqlite3 gettext rclone unattended-upgrades
sudo adduser --system --group --home /srv/blog --shell /bin/bash blog
sudo usermod -aG www-data blog
sudo mkdir -p /srv/blog/{data,media,staticfiles,backups}
sudo chown -R blog:www-data /srv/blog
sudo chmod 750 /srv/blog
```

## 3. Código y entorno

Como el repo es privado, crea una *deploy key* de solo lectura:

```bash
sudo -iu blog
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub   # pégala en GitHub → repo → Settings → Deploy keys
git clone git@github.com:NestorBracho/blogweb.git /srv/blog/app
python3 -m venv /srv/blog/venv
/srv/blog/venv/bin/pip install -r /srv/blog/app/requirements.txt
cp /srv/blog/app/.env.example /srv/blog/app/.env
chmod 600 /srv/blog/app/.env
nano /srv/blog/app/.env     # rellena todo (SECRET_KEY nueva, dominio, email, ADMIN_URL...)
```

## 4. Subir la base de datos y las imágenes actuales

Desde **tu Mac** (en la carpeta del proyecto):

```bash
scp db.sqlite3 ubuntu@IP_DEL_SERVIDOR:/tmp/db.sqlite3
tar -czf /tmp/media.tar.gz media
scp /tmp/media.tar.gz ubuntu@IP_DEL_SERVIDOR:/tmp/
```

En el servidor:

```bash
sudo mv /tmp/db.sqlite3 /srv/blog/data/db.sqlite3
sudo tar -xzf /tmp/media.tar.gz -C /srv/blog
sudo chown -R blog:www-data /srv/blog/data /srv/blog/media
sudo -iu blog bash -c 'cd /srv/blog/app && ../venv/bin/python manage.py migrate && ../venv/bin/python manage.py collectstatic --noinput && ../venv/bin/python manage.py check --deploy'
```

> Las portadas subidas antes a S3 no están en tu `media/` local. Si alguna falta,
> descárgala del bucket o vuelve a subirla desde el admin.

Las portadas se guardan, además, al tamaño de cada sitio de la web en `media/covers/` (ver `blog/covers.py`). Un post
nuevo las genera al guardarse; para las que ya había, o si cambias los tamaños, genéralas con:

```bash
sudo -iu blog bash -c 'cd /srv/blog/app && ../venv/bin/python manage.py make_cover_sizes'
```

## 5. Gunicorn (systemd)

```bash
sudo cp /srv/blog/app/deploy/gunicorn.service /etc/systemd/system/blog.service
sudo systemctl daemon-reload
sudo systemctl enable --now blog
sudo systemctl status blog
```

Permite al usuario `blog` recargar y reiniciar el servicio (lo usa `deploy/update.sh`). El fichero se valida con
`visudo` antes de instalarlo, porque un error en `/etc/sudoers.d` deja `sudo` inservible:

```bash
echo 'blog ALL=(root) NOPASSWD: /usr/bin/systemctl reload-or-restart blog, /usr/bin/systemctl restart blog' > /tmp/blog.sudoers
sudo visudo -cf /tmp/blog.sudoers && sudo install -m 440 /tmp/blog.sudoers /etc/sudoers.d/blog
```

## 6. Cloudflare + nginx

1. Añade tu dominio a Cloudflare (plan Free) y cambia los nameservers en tu registrador.
2. DNS: registro `A` para `@` y otro para `www` → IP del servidor, **proxied** (nube naranja).
3. *SSL/TLS → Overview*: modo **Full (strict)**.
4. *SSL/TLS → Origin Server → Create Certificate* (15 años). Guarda ambos en el servidor:

```bash
sudo mkdir -p /etc/ssl/cloudflare
sudo nano /etc/ssl/cloudflare/origin.pem   # certificado
sudo nano /etc/ssl/cloudflare/origin.key   # clave privada
sudo chmod 600 /etc/ssl/cloudflare/origin.key
```

5. Configura nginx (cambia `tudominio.com` por el tuyo):

```bash
sudo cp /srv/blog/app/deploy/nginx.conf /etc/nginx/sites-available/blog
sudo sed -i 's/tudominio.com/TU-DOMINIO/g' /etc/nginx/sites-available/blog
sudo ln -s /etc/nginx/sites-available/blog /etc/nginx/sites-enabled/blog
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

6. Opcional pero recomendado: *Zero Trust → Access* para proteger la URL del admin
   con un código enviado a tu email.

## 7. Email y avisos

Crea una cuenta en Brevo o Resend, verifica tu dominio (añaden registros SPF/DKIM en
Cloudflare DNS) y pon las credenciales SMTP en `.env`. Prueba:

```bash
sudo -iu blog bash -c 'cd /srv/blog/app && ../venv/bin/python manage.py sendtestemail tu@email.com'
```

### Avisos

Con `ADMINS` en `.env` (una dirección, o varias separadas por comas), el servidor avisa por email, por ese mismo SMTP:

- De cada error de servidor (una página que da 500), con la traza. El mismo error llega como mucho una vez por hora
  y worker, para no gastar la cuota diaria del SMTP (300 en el plan gratuito de Brevo), que comparte con el
  formulario de contacto y la newsletter. `journalctl -u blog` los tiene todos.
- De cada copia nocturna que falle (`backup.sh`, paso 8), con el paso que falló.

Sin `ADMINS` no avisa de nada. Después de añadirla, recarga la web para que la lea y prueba los dos avisos:

```bash
sudo systemctl reload blog
sudo -iu blog bash -c 'cd /srv/blog/app && ../venv/bin/python manage.py sendtestemail --admins'
sudo -iu blog bash -c 'cd /srv/blog/app && ../venv/bin/python manage.py email_admins "Prueba" "Los avisos llegan"'
```

Si la web deja de responder, avisa GitHub: el workflow [`uptime.yml`](../.github/workflows/uptime.yml) pide `/en/` y
`/` cada 30 minutos, y si fallan, el run falla y GitHub manda un email a quien cambió por última vez su línea `cron`
(tú, al fusionar). En GitHub, *Settings → Notifications → Actions* debe tener el email activado para los workflows
que fallan. En un repo público, GitHub **desactiva los workflows programados tras 60 días sin actividad** en el
repo; si pasa, vuelve a activarlo en *Actions → Uptime → Enable workflow*.

## 8. Backups

```bash
sudo chmod +x /srv/blog/app/deploy/backup.sh
sudo -u blog crontab -e
# añade:
30 3 * * * /srv/blog/app/deploy/backup.sh >> /srv/blog/backups/backup.log 2>&1
```

Cada noche el script guarda la base de datos y `media/` en `/srv/blog/backups` (conserva 14 días). Si existe un
remote de rclone llamado `backup`, además los sube a Google Drive y conserva allí 30 días
([ADR 5](../docs/adr/0005-off-site-backups-to-google-drive.md)). Sin ese remote, avisa en `backup.log` y las copias
se quedan solo en el servidor. Si falla algún paso, la copia o la subida, envía un email a `ADMINS`
([Avisos](#avisos)) con el comando que falló.

### Copia en Google Drive

El servidor no tiene navegador, así que la autorización se reparte entre el servidor y tu ordenador:

1. En tu ordenador, instala rclone: `brew install rclone` (o mira <https://rclone.org/install/>).
2. En el servidor, `sudo -iu blog rclone config`, y responde:
   - `n` (nuevo remote), nombre `backup` y tipo `drive`;
   - `client_id` y `client_secret`: Enter, vacíos;
   - `scope`: `drive.file`. Así rclone solo ve los archivos que crea él, no el resto de tu Drive;
   - `service_account_file`: Enter. "Edit advanced config?": `n`;
   - "Use web browser to automatically authenticate?": `n`. Muestra un comando `rclone authorize "drive" "…"`.
3. Ejecuta ese comando en tu ordenador. Se abre el navegador: entra con tu cuenta de Google y acepta. Copia el token
   que imprime la terminal.
4. Pégalo en el servidor, en `config_token>`. Responde `n` a "Configure this as a Shared Drive", `y` para guardar y
   `q` para salir.
5. Prueba:

   ```bash
   sudo -iu blog /srv/blog/app/deploy/backup.sh
   sudo -iu blog rclone ls backup:blog-backups
   ```

Si algún día falla la subida (por ejemplo, porque revocaste el acceso en tu cuenta de Google), te llega un email y
`backup.log` dice por qué. Para volver a autorizar: `sudo -iu blog rclone config reconnect backup:`.

### Restaurar

Una copia solo cuenta si se puede restaurar. Para la base de datos, con la fecha que quieras recuperar:

```bash
sudo -iu blog rclone copy backup:blog-backups /tmp/restore --include "db-2026-10-14.sqlite3.gz"
sudo -iu blog bash -c 'gunzip /tmp/restore/db-2026-10-14.sqlite3.gz && sqlite3 /tmp/restore/db-2026-10-14.sqlite3 "PRAGMA integrity_check;"'
# Si dice "ok", sustitúyela con el servicio parado (y sin los -wal/-shm de la base de datos anterior):
sudo systemctl stop blog
sudo -u blog mv /srv/blog/data/db.sqlite3 /srv/blog/data/db.sqlite3.old
sudo -u blog rm -f /srv/blog/data/db.sqlite3-wal /srv/blog/data/db.sqlite3-shm
sudo -u blog cp /tmp/restore/db-2026-10-14.sqlite3 /srv/blog/data/db.sqlite3
sudo systemctl start blog
```

Las imágenes: `sudo -u blog tar -xzf media-FECHA.tar.gz -C /srv/blog`, tras descargar el archivo de la misma forma.

## 9. Actualizar la web

```bash
sudo -iu blog /srv/blog/app/deploy/update.sh
```

El script recarga Gunicorn sin cortar la web: `systemctl reload` le manda `HUP`, el socket sigue abierto, los workers
nuevos cargan el código nuevo y los viejos terminan las peticiones que tenían a medias. Lo que llega mientras tanto
espera un momento en vez de dar 502. Solo reinicia del todo cuando se actualiza el propio Gunicorn, porque el proceso
maestro sigue ejecutando la versión con la que arrancó; ese despliegue sí corta unos segundos.

Si cambias `gunicorn.service`, cópialo otra vez a `/etc/systemd/system/blog.service` (en Google Cloud, con el `sed`
de los workers) y ejecuta `sudo systemctl daemon-reload`. Un cambio en `ExecStart` necesita además
`sudo systemctl restart blog`.

## Problemas frecuentes

| Síntoma | Revisa |
|---|---|
| 502 Bad Gateway | `sudo journalctl -u blog -n 50` |
| 400 Bad Request | `ALLOWED_HOSTS` en `.env` |
| 403 CSRF al hacer login/enviar formularios | `CSRF_TRUSTED_ORIGINS` con `https://` |
| Bucle de redirecciones | Cloudflare debe estar en **Full (strict)**, no en *Flexible* |
| No carga nada desde fuera | Security List **y** iptables (paso 1.4 y 2) |
| Error 522 de Cloudflare (GCP) | Rangos de Cloudflare en la regla `allow-web` desactualizados |
| Imágenes 404 | Permisos de `/srv/blog/media` (grupo `www-data`) |
| Algo deja de cargar y la consola del navegador dice "Content Security Policy" | `SECURE_CSP` en `config/settings.py`. Solo admite scripts del propio sitio: Rocket Loader, Web Analytics o Bot Fight Mode de Cloudflare inyectan los suyos |

---

## Google Cloud (e2-micro)

Lo que cambia respecto a Oracle (el resto de la guía, desde el paso 2, es igual):

- **Gratis solo si** la VM es `e2-micro`, está en `us-west1`, `us-central1` o `us-east1`,
  y el disco es `pd-standard` de ≤ 30 GB. Una sola VM.
- **Crear la VM** desde Cloud Shell (`https://shell.cloud.google.com`):

  ```bash
  # 80/443 solo desde Cloudflare: nadie puede saltárselo atacando la IP directamente
  CLOUDFLARE_IPS=$(curl -sf https://www.cloudflare.com/ips-v4 | paste -sd, -)
  test -n "$CLOUDFLARE_IPS" && gcloud compute firewall-rules create allow-web --allow=tcp:80,tcp:443 \
    --source-ranges="$CLOUDFLARE_IPS" --target-tags=http-server,https-server \
    --description="HTTP(S) only from Cloudflare: https://www.cloudflare.com/ips-v4"
  # La red default abre el escritorio remoto de Windows a todo internet; en Linux sobra
  gcloud compute firewall-rules delete default-allow-rdp
  gcloud compute instances create blog-nestorbracho \
    --zone=us-east1-b --machine-type=e2-micro \
    --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud \
    --boot-disk-size=30GB --boot-disk-type=pd-standard \
    --tags=http-server,https-server \
    --metadata=ssh-keys="nestor:$(cat ~/.ssh/oracle-blog.pub)"
  ```

- **No hace falta tocar iptables** (paso 2): el firewall lo gestiona la regla `allow-web`.
- **Rangos de Cloudflare**: cambian muy de vez en cuando. Si Cloudflare publica rangos nuevos
  (o la web da error 522), actualiza la regla:

  ```bash
  CLOUDFLARE_IPS=$(curl -sf https://www.cloudflare.com/ips-v4 | paste -sd, -)
  test -n "$CLOUDFLARE_IPS" && gcloud compute firewall-rules update allow-web --source-ranges="$CLOUDFLARE_IPS"
  ```

  Para comprobarlo, la IP directa no debe responder y el dominio sí:
  `curl -k --connect-timeout 5 https://IP_DEL_SERVIDOR` debe agotar el tiempo.
- **Swap obligatorio** (1 GB de RAM):

  ```bash
  sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-swappiness.conf
  ```

- **Gunicorn con 2 workers**: `sed 's/--workers 3/--workers 2/'` al copiar `gunicorn.service`.
- **Repo público**: se clona por HTTPS, sin deploy key.
- **Certificado de origen** generado con CSR propia para que la clave privada no salga del servidor:

  ```bash
  sudo openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes \
    -keyout /etc/ssl/cloudflare/origin.key -out /etc/ssl/cloudflare/origin.csr -subj "/CN=nestorbracho.com"
  ```

  En Cloudflare: *SSL/TLS → Origin Server → Create Certificate → Use my private key and CSR*,
  pega la CSR y guarda el certificado resultante en `/etc/ssl/cloudflare/origin.pem`.
- **Tráfico de salida**: el plan gratuito incluye 1 GB/mes. Cloudflare cachea estáticos e
  imágenes, así que la mayor parte del tráfico no sale de la VM.
- **Fin del periodo de prueba (90 días)**: para que la VM siga encendida hay que pasar la
  cuenta de facturación a pago ("Upgrade"). Mientras solo uses recursos Always Free no hay cargos.

Acceso SSH:

```bash
ssh -i ~/.ssh/oracle-blog nestor@IP_DEL_SERVIDOR
```

---

## CI/CD (GitHub Actions)

`.github/workflows/deploy.yml`:

- **Pull requests y pushes a `main`**: `ruff` (lint y formato), `manage.py check`,
  migraciones pendientes, `migrate` sobre una base de datos vacía, los tests con informe de
  cobertura (también en el resumen del job) y `collectstatic` en modo producción.
- **Push/merge a `main`** (si lo anterior pasa): se conecta por SSH como `blog`, ejecuta
  `deploy/update.sh` y comprueba que `https://nestorbracho.com/en/` responde 200 y que
  `https://nestorbracho.com` redirige a `/en/` (las páginas llevan el idioma en la URL).

La clave de GitHub está **restringida en el servidor** (`restrict,command=".../update.sh"` en
`/srv/blog/.ssh/authorized_keys`): solo puede lanzar el deploy, no abrir una shell.

Configuración inicial (una sola vez, desde tu Mac):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github-deploy -N "" -C "github-actions-deploy"
ssh -i ~/.ssh/oracle-blog nestor@IP_DEL_SERVIDOR "sudo -u blog install -d -m 700 /srv/blog/.ssh && echo 'restrict,command=\"/srv/blog/app/deploy/update.sh\" $(cat ~/.ssh/github-deploy.pub)' | sudo -u blog tee -a /srv/blog/.ssh/authorized_keys >/dev/null && sudo chmod 600 /srv/blog/.ssh/authorized_keys"
gh secret set DEPLOY_SSH_KEY < ~/.ssh/github-deploy
gh secret set DEPLOY_HOST --body IP_DEL_SERVIDOR
ssh-keyscan -t ed25519 IP_DEL_SERVIDOR | gh secret set DEPLOY_KNOWN_HOSTS
```

Para revocar el acceso de GitHub: borra la línea correspondiente de
`/srv/blog/.ssh/authorized_keys` y el secreto `DEPLOY_SSH_KEY`.
