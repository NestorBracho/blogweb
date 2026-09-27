# Despliegue en Oracle Cloud (Always Free)

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

## 5. Gunicorn (systemd)

```bash
sudo cp /srv/blog/app/deploy/gunicorn.service /etc/systemd/system/blog.service
sudo systemctl daemon-reload
sudo systemctl enable --now blog
sudo systemctl status blog
```

Permite al usuario `blog` reiniciar el servicio (lo usa `deploy/update.sh`):

```bash
echo 'blog ALL=(root) NOPASSWD: /usr/bin/systemctl restart blog' | sudo tee /etc/sudoers.d/blog
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

## 7. Email

Crea una cuenta en Brevo o Resend, verifica tu dominio (añaden registros SPF/DKIM en
Cloudflare DNS) y pon las credenciales SMTP en `.env`. Prueba:

```bash
sudo -iu blog bash -c 'cd /srv/blog/app && ../venv/bin/python manage.py sendtestemail tu@email.com'
```

## 8. Backups

```bash
sudo chmod +x /srv/blog/app/deploy/backup.sh
sudo -u blog crontab -e
# añade:
30 3 * * * /srv/blog/app/deploy/backup.sh >> /srv/blog/backups/backup.log 2>&1
```

Para copiarlos fuera del servidor, configura un remote de rclone llamado `backup`
(`sudo -iu blog rclone config`), por ejemplo Cloudflare R2 u Oracle Object Storage
(ambos tienen capa gratuita). El script lo detecta automáticamente.

## 9. Actualizar la web

```bash
sudo -iu blog /srv/blog/app/deploy/update.sh
```

## Problemas frecuentes

| Síntoma | Revisa |
|---|---|
| 502 Bad Gateway | `sudo journalctl -u blog -n 50` |
| 400 Bad Request | `ALLOWED_HOSTS` en `.env` |
| 403 CSRF al hacer login/enviar formularios | `CSRF_TRUSTED_ORIGINS` con `https://` |
| Bucle de redirecciones | Cloudflare debe estar en **Full (strict)**, no en *Flexible* |
| No carga nada desde fuera | Security List **y** iptables (paso 1.4 y 2) |
| Imágenes 404 | Permisos de `/srv/blog/media` (grupo `www-data`) |
