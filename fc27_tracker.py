import os
import re
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# --- VOS 2 PARAMÈTRES À PERSONNALISER ---
PRIX_CIBLE = 30.00  # Laissez 30.00 pour tester !
SUJET_NTFY = "alertefc27"  # Mettez ici le nom EXACT de votre canal dans l'appli ntfy

URL_PRODUIT = "https://www.allkeyshop.com/blog/buy-ea-sports-fc-27-steam-account-compare-prices/"

def envoyer_ntfy(titre, message):
    url = f"https://ntfy.sh/{SUJET_NTFY.strip()}"
    r = requests.post(
        url,
        data=message.encode("utf-8"),
        headers={"Title": titre, "Priority": "high"}
    )
    print(f"Notification envoyée vers {url} (Statut HTTP : {r.status_code})")

def extraire_meilleur_prix():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            locale="fr-FR"
        )
        page = context.new_page()
        print("Ouverture de la page dans le navigateur...")
        page.goto(URL_PRODUIT, wait_until="domcontentloaded", timeout=45000)
        
        # Attend 6 secondes que le tableau JavaScript des vendeurs se charge complètement
        page.wait_for_timeout(6000)
        html = page.content()
        texte = page.inner_text("body")
        browser.close()

    # On coupe après MERCHANT et avant le TOP 50 pour ne garder que les offres de FC 27
    if "MERCHANT" in texte:
        texte = texte.split("MERCHANT", 1)[1]
    for fin in ["Show all offers", "Historical Lowest Prices", "TOP 50"]:
        if fin in texte:
            texte = texte.split(fin, 1)[0]

    prix_trouves = []
    for ligne in texte.split("\n"):
        ligne = ligne.strip()
        # Ignore les frais (+3.26€) et cherche les prix en € ou $
        if not ligne.startswith("+"):
            m = re.search(r'^(\d+[\.,]\d{2})\s*(?:€|\$|EUR|USD)?$', ligne)
            if m:
                val = float(m.group(1).replace(",", "."))
                if 12.0 <= val <= 150.0:
                    prix_trouves.append(val)

    # Secours : recherche directe dans le code HTML si le formatage diffère
    if not prix_trouves:
        for m in re.finditer(r'(\d{2}[\.,]\d{2})\s*€', html):
            val = float(m.group(1).replace(",", "."))
            if 12.0 <= val <= 150.0:
                prix_trouves.append(val)

    return min(prix_trouves) if prix_trouves else None

if __name__ == "__main__":
    # Si vous avez cliqué sur "Run workflow" manuellement, on envoie un test sur votre téléphone !
    if os.environ.get("EVENT_NAME") == "workflow_dispatch":
        print("Lancement manuel détecté : envoi d'une notification de test sur ntfy...")
        envoyer_ntfy("Test GitHub OK", "Votre téléphone est bien relié au robot GitHub !")

    prix = extraire_meilleur_prix()
    if prix:
        print(f"✅ Meilleur prix trouvé : {prix:.2f} € (Seuil : {PRIX_CIBLE:.2f} €)")
        if prix <= PRIX_CIBLE:
            print("🚨 Seuil atteint ! Envoi de l'alerte de prix...")
            envoyer_ntfy(
                "ALERTE PRIX : EA SPORTS FC 27",
                f"Meilleur prix détecté : {prix:.2f} € (Seuil : {PRIX_CIBLE:.2f} €)\n{URL_PRODUIT}"
            )
    else:
        print("⚠️ Aucun prix détecté sur la page.")
