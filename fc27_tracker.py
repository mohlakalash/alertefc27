import re
import json
import requests
from bs4 import BeautifulSoup

# --- VOS 2 PARAMÈTRES À PERSONNALISER ---
PRIX_CIBLE = 30.00  # Laissez 30.00 pour tester !
SUJET_NTFY = "alertefc27"  # Votre nom de canal ntfy exact

URL_PRODUIT = "https://www.allkeyshop.com/blog/buy-ea-sports-fc-27-steam-account-compare-prices/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cookie": "aks_currency=EUR; currency=EUR"
}

def envoyer_ntfy(titre, message):
    requests.post(
        f"https://ntfy.sh/{SUJET_NTFY.strip()}",
        data=message.encode("utf-8"),
        headers={"Title": titre, "Priority": "high"}
    )

def extraire_meilleur_prix(html):
    prix_candidats = []

    # Méthode 1 : Chercher dans les données structurées JSON-LD (lowPrice / price)
    for m in re.finditer(r'"(?:lowPrice|price)"\s*:\s*"?(\d+(?:\.\d+)?)"?', html):
        val = float(m.group(1))
        if 10.0 <= val <= 150.0:
            prix_candidats.append(val)

    # Méthode 2 : Chercher dans les variables JavaScript / HTML d'AllKeyShop (data-price, etc.)
    for m in re.finditer(r'(?:data-price|price_eur|"price")\s*[=:]\s*"?(\d+\.\d{2})"?', html):
        val = float(m.group(1))
        if 10.0 <= val <= 150.0:
            prix_candidats.append(val)

    # Méthode 3 : Chercher tous les prix affichés dans le tableau des offres (€ ou $)
    soup = BeautifulSoup(html, "html.parser")
    texte = soup.get_text(separator="\n")
    if "MERCHANT" in texte:
        texte = texte.split("MERCHANT", 1)[1]
    if "Historical Lowest Prices" in texte:
        texte = texte.split("Historical Lowest Prices", 1)[0]

    for ligne in texte.split("\n"):
        ligne = ligne.strip()
        if not ligne.startswith("+"):
            m = re.search(r'(\d+[\.,]\d{2})\s*(?:€|\$|EUR)', ligne)
            if m:
                val = float(m.group(1).replace(',', '.'))
                if 10.0 <= val <= 150.0:
                    prix_candidats.append(val)

    return min(prix_candidats) if prix_candidats else None

if __name__ == "__main__":
    print("Vérification de la page AllKeyShop en cours...")
    r = requests.get(URL_PRODUIT, headers=HEADERS, timeout=20)
    print(f"Code HTTP : {r.status_code} | Taille de la page : {len(r.text)} caractères")

    if r.status_code == 200:
        prix = extraire_meilleur_prix(r.text)
        if prix:
            print(f"✅ Meilleur prix trouvé : {prix:.2f} € (Seuil fixé : {PRIX_CIBLE:.2f} €)")
            if prix <= PRIX_CIBLE:
                print("🚨 Seuil atteint ! Envoi de la notification sur ntfy...")
                envoyer_ntfy(
                    "ALERTE PRIX : EA SPORTS FC 27",
                    f"Meilleur prix détecté : {prix:.2f} € (Seuil : {PRIX_CIBLE:.2f} €)\n{URL_PRODUIT}"
                )
        else:
            # Affiche un aperçu du contenu reçu pour comprendre ce que voit GitHub
            soup = BeautifulSoup(r.text, "html.parser")
            apercu = " ".join(soup.get_text().split())[:300]
            print(f"⚠️ Aucun prix trouvé. Aperçu de la page reçue : {apercu}")
    else:
        print(f"⚠️ Erreur HTTP {r.status_code}")
