# Running the website on Oracle Cloud (Always Free)

This puts the whole website (public pages and the `/admin` editor) on a free Oracle Cloud
server, at your own domain with HTTPS. Until step 6, arcooling.in keeps running on GitHub
Pages exactly as now, so nothing breaks while you set this up.

**What it costs:** ₹0 on the Always Free tier. Oracle asks for a card to verify your
identity; Always Free resources are not charged. Stay on Always Free shapes (below) and
don't upgrade the account to "Pay As You Go" unless you mean to.

## 0. Test it on your PC first

```
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python serve.py        # open http://127.0.0.1:8080
```

This is the same server program (Waitress) the Oracle server runs. It uses your `.env`
and your local database (`instance/ar_cooling.db`). Press Ctrl+C to stop it.

## 1. Create the Oracle Cloud account

1. Go to https://www.oracle.com/cloud/free/ and click **Start for free**.
2. **Home region:** pick **India South (Hyderabad)**, the closest to your customers.
   It can't be changed later. If Hyderabad has no free capacity, Mumbai is fine.
3. Verify your email, phone and card. Wait for the "account is ready" email.

## 2. Create the server

1. In the console: **☰ Menu → Compute → Instances → Create instance**.
2. **Name:** `ar-cooling`.
3. **Image and shape → Edit:**
   - Image: **Canonical Ubuntu 24.04**.
   - Shape: **Ampere → VM.Standard.A1.Flex**, 1 OCPU and 6 GB memory (Always Free).
     If it says "out of capacity", try again later, or use **VM.Standard.E2.1.Micro**
     (also Always Free; smaller but enough for this site).
4. **Networking:** keep "Create new virtual cloud network" and **Assign a public IPv4 address**.
5. **Add SSH keys:** choose **Generate a key pair for me** and click **Save private key**.
   Keep this file safe: it is the only way into the server.
6. Click **Create**. When it shows **Running**, copy its **Public IP address**.

## 3. Open the web ports in Oracle's network

1. On the instance page, click the **subnet** link, then the **Default Security List**.
2. **Add Ingress Rules**, twice:
   - Source CIDR `0.0.0.0/0`, IP protocol TCP, destination port `80`
   - Source CIDR `0.0.0.0/0`, IP protocol TCP, destination port `443`

## 4. Connect to the server

From PowerShell on your PC (use the key file you saved and the server's IP):

```
ssh -i C:\path\to\ssh-key.key ubuntu@<server IP>
```

Type `yes` the first time. If it says the key's permissions are too open, run
`icacls C:\path\to\ssh-key.key /inheritance:r /grant:r "$($env:USERNAME):R"` and try again.

## 5. Install the website

On the server (the second argument is the git branch; use `main` once this is merged):

```
curl -fsSL https://raw.githubusercontent.com/AbdulRaheem-Sheik/ar-cooling-solutions/feature/oracle-cloud/deploy/oracle/setup.sh -o setup.sh
sudo bash setup.sh arcooling.in feature/oracle-cloud
```

It takes a few minutes and ends with **"Done. The website is running."** Open
`http://<server IP>` in your browser: you should see the site.

Turn on the admin login:

```
sudo nano /etc/ar-cooling.env        # fill in AR_ADMIN_USERNAME and AR_ADMIN_PASSWORD (12+ characters)
sudo systemctl restart ar-cooling
```

(In nano: Ctrl+O, Enter to save; Ctrl+X to exit.)

## 6. Point arcooling.in at the server (go live)

Only do this once step 5 works. At your domain registrar's DNS settings:

- Change the **A** record for `arcooling.in` (`@`) to the server's IP. Remove the old
  GitHub Pages A records (185.199.108–111.153).
- Change `www` to an **A** record with the same IP (or a CNAME to `arcooling.in`).

Within minutes to a few hours, https://arcooling.in loads from your server; Caddy gets
the HTTPS certificate by itself. Then in GitHub, **Settings → Pages**, unpublish the
site (or keep it as a fallback until you're confident).

## Day to day

| Task | Command (on the server) |
|---|---|
| Deploy new code from GitHub | `sudo bash /opt/ar-cooling/deploy/oracle/setup.sh arcooling.in main` |
| See the app's logs | `sudo journalctl -u ar-cooling -f` |
| Restart the app | `sudo systemctl restart ar-cooling` |
| Back up the database to your PC | from PowerShell: `scp -i <key> ubuntu@<IP>:/var/lib/ar-cooling/ar_cooling.db .` |

Admin edits live in the server's database (`/var/lib/ar-cooling/ar_cooling.db`), which
updates never touch. Changes you push to `data/` in git only reach a database that is
empty; to load them over existing content, run on the server:
```
sudo -u arcooling AR_DATABASE_PATH=/var/lib/ar-cooling/ar_cooling.db /opt/ar-cooling/.venv/bin/python /opt/ar-cooling/store.py import --replace
```

This discards admin edits made on the server, so back up the database first.
