# Vaibhav Garments — WhatsApp Ordering Website

A Flask clothing storefront with Women / Men / Kids categories, product search, product detail pages, a customer details form, WhatsApp order handoff, and an admin panel. There is **no cart and no online payment checkout**.

## Local setup (Windows / VS Code)

1. Install Python 3.11 or newer.
2. Extract the ZIP and open the `Vaibhav_Garments_WhatsApp_Store` folder in VS Code.
3. Open Terminal in VS Code and run:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python app.py
   ```

   If PowerShell blocks activation, use Command Prompt terminal and run `.venv\Scripts\activate.bat`, or run `.venv\Scripts\python.exe -m pip install -r requirements.txt` then `.venv\Scripts\python.exe app.py`.

4. Open `http://127.0.0.1:5000`.

## Admin login for local preview

- URL: `http://127.0.0.1:5000/admin/login`
- Username: `admin`
- Password: `ChangeMe123!`

Change these credentials before a public deployment by setting `ADMIN_USERNAME` and a strong `ADMIN_PASSWORD` environment variable. The admin password is stored as a password hash. Never publish your secret keys.

## Admin panel

- Open `/admin/login`, sign in, and add/edit/delete products.
- Product fields include name, category, current/old price, description, fabric, sizes, colours, image, featured status and visibility.
- Shop settings page lets you change WhatsApp, Instagram and address for the current running process. For a persistent live deployment, set the matching environment variables in Render.

## WhatsApp ordering

Each product has a **Buy on WhatsApp** action. The customer fills name, mobile, delivery address, city, pincode, size, colour, fabric, quantity and optional note. The site opens WhatsApp with a pre-filled order message containing product name, category, price, quantity, total estimate, customer details and public product/image URLs.

WhatsApp's normal `wa.me` link cannot silently attach an image file. It sends a product image URL/reference in the message; the customer can open the product page to view it. Automatically attaching media requires a separate WhatsApp Business API integration.

## Deploying on Render

1. Push the extracted project to a new GitHub repository.
2. In Render, create a **Web Service** from that repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Set environment variables: `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `WHATSAPP_NUMBER`, `INSTAGRAM_URL`, `SHOP_ADDRESS`.
6. Add a Render persistent disk mounted at `/var/data` if you want SQLite and uploaded images to persist across deploys/restarts. Set `DATABASE_PATH=/var/data/store.db` and adjust upload storage to a persistent disk before relying on it for a live store. Without persistent storage, SQLite data and uploaded images can be lost on redeploy/restart.

## Before handing over to a client

- Change the default admin password.
- Test orders on a real phone/WhatsApp account.
- Add the client's real product photos and correct prices/stock.
- Confirm delivery charges, return policy, privacy policy and business contact details.
- Test the site on mobile.
- Configure persistent storage/backups and a custom domain if required.
