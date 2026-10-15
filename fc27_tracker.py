import re
import requests
from playwright.sync_api import sync_playwright

# --- VOTRE CANAL NTFY ---
SUJET_NTFY = "alertefc27_8906612"  # Mettez ici le nom EXACT de votre canal dans l'appli ntfy

URL_PRODUIT = "https://www.allkeyshop.com/blog/buy-ea-sports-fc-27-steam-account-compare-prices/"

def envoyer_ntfy(titre, message):
    url = f"https://ntfy.sh/{SUJET_NTFY.strip()}"
    r = requests.post(
        url,
        data=message.encode("utf-8"),
        headers={"Title": titre, "Priority": "default"}
    )
    print(f"Notification envoyée (Statut HTTP : {r.status_code})")

def extraire_meilleur_prix():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            locale="fr-FR"
        )
        page = context.new_page()
        page.goto(URL_PRODUIT, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(6000)  # Attend 6s que le tableau des prix JavaScript s'affiche
        
        html = page.content()
        texte = page.inner_text("body")
        browser.close()

    if "MERCHANT" in texte:
        texte = texte.split("MERCHANT", 1)[1]
    for fin in ["Show all offers", "Historical Lowest Prices", "TOP 50"]:
        if fin in texte:
            texte = texte.split(fin, 1)[0]

    prix_trouves = []
    for ligne in texte.split("\n"):
        ligne = ligne.strip()
        if not ligne.startswith("+"):
            m = re.search(r'^(\d+[\.,]\d{2})\s*(?:€|\$|EUR|USD)?$', ligne)
            if m:
                val = float(m.group(1).replace(",", "."))
                if 12.0 <= val <= 150.0:
                    prix_trouves.append(val)

    if not prix_trouves:
        for m in re.finditer(r'(\d{2}[\.,]\d{2})\s*€', html):
            val = float(m.group(1).replace(",", "."))
            if 12.0 <= val <= 150.0:
                prix_trouves.append(val)

    return min(prix_trouves) if prix_trouves else None

if __name__ == "__main__":
    prix = extraire_meilleur_prix()
    if prix:
        print(f"✅ Prix le moins cher relevé : {prix:.2f} €")
        envoyer_ntfy(
            f"FC 27 : {prix:.2f} €",
            f"Prix le moins cher actuel : {prix:.2f} €\n{URL_PRODUIT}"
        )
    else:
        print("⚠️ Aucun prix détecté sur la page.")
