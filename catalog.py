"""Catálogo de activos para el menú de exploración: mercado -> sector -> tickers.

Para agregar un activo basta con añadir (ticker, nombre) en el sector correspondiente.
Los tickers son los de Yahoo! Finance.
"""
from __future__ import annotations

# Las emisoras del SIC se analizan con su ticker de origen (EE.UU.), que tiene más
# historia e intradía que su réplica en la BMV; las señales técnicas son equivalentes.
MARKETS: dict[str, dict] = {
    "MX": {
        "name": "Mercado mexicano (BMV)",
        "sectors": [
            ("Financiero", [("GFNORTEO.MX", "Banorte"), ("GFINBURO.MX", "Inbursa"),
                            ("BBAJIOO.MX", "BanBajío"), ("Q.MX", "Quálitas"),
                            ("GENTERA.MX", "Gentera"), ("RA.MX", "Regional")]),
            ("Consumo", [("WALMEX.MX", "Walmart de México"), ("FEMSAUBD.MX", "FEMSA"),
                         ("BIMBOA.MX", "Bimbo"), ("KOFUBL.MX", "Coca-Cola FEMSA"),
                         ("AC.MX", "Arca Continental"), ("GRUMAB.MX", "Gruma"),
                         ("KIMBERA.MX", "Kimberly-Clark MX"), ("LIVEPOLC-1.MX", "Liverpool"),
                         ("CHDRAUIB.MX", "Chedraui")]),
            ("Materiales e industria", [("CEMEXCPO.MX", "Cemex"), ("GMEXICOB.MX", "Grupo México"),
                                        ("ORBIA.MX", "Orbia"), ("ALPEKA.MX", "Alpek"),
                                        ("GCC.MX", "GCC")]),
            ("Telecom y medios", [("AMXB.MX", "América Móvil"), ("TLEVISACPO.MX", "Televisa")]),
            ("Aeropuertos e infraestructura", [("GAPB.MX", "GAP"), ("ASURB.MX", "ASUR"),
                                               ("OMAB.MX", "OMA"), ("PINFRA.MX", "Pinfra")]),
            ("FIBRAs e inmobiliario", [("FUNO11.MX", "Fibra Uno"), ("FIBRAPL14.MX", "Fibra Prologis"),
                                       ("FMTY14.MX", "Fibra Monterrey"), ("VESTA.MX", "Vesta")]),
        ],
    },
    "SIC": {
        "name": "SIC (acciones globales)",
        "sectors": [
            ("Tecnología", [("AAPL", "Apple"), ("MSFT", "Microsoft"), ("NVDA", "Nvidia"),
                            ("GOOGL", "Alphabet"), ("META", "Meta"), ("AMD", "AMD")]),
            ("Consumo", [("AMZN", "Amazon"), ("TSLA", "Tesla"), ("KO", "Coca-Cola"),
                         ("PEP", "PepsiCo"), ("MCD", "McDonald's"), ("NKE", "Nike"),
                         ("WMT", "Walmart"), ("COST", "Costco")]),
            ("Financiero", [("JPM", "JPMorgan"), ("BAC", "Bank of America"), ("GS", "Goldman Sachs"),
                            ("V", "Visa"), ("MA", "Mastercard"), ("BRK-B", "Berkshire")]),
            ("Salud", [("JNJ", "Johnson & Johnson"), ("PFE", "Pfizer"), ("UNH", "UnitedHealth"),
                       ("LLY", "Eli Lilly"), ("ABBV", "AbbVie")]),
            ("Energía e industria", [("XOM", "Exxon"), ("CVX", "Chevron"), ("BA", "Boeing"),
                                     ("CAT", "Caterpillar"), ("GE", "GE Aerospace")]),
            ("Entretenimiento", [("NFLX", "Netflix"), ("DIS", "Disney")]),
        ],
    },
    "ETF": {
        "name": "ETFs",
        "sectors": [
            ("Índices", [("SPY", "S&P 500"), ("VOO", "S&P 500 Vanguard"), ("QQQ", "Nasdaq 100"),
                         ("DIA", "Dow Jones"), ("IWM", "Russell 2000"),
                         ("NAFTRACISHRS.MX", "NAFTRAC (IPC México)")]),
            ("Sectoriales", [("XLK", "Tecnología"), ("XLF", "Financiero"), ("XLE", "Energía"),
                             ("XLV", "Salud"), ("XLY", "Consumo discrecional"), ("XLI", "Industrial")]),
            ("Internacionales", [("EWW", "México"), ("EEM", "Emergentes"), ("EWZ", "Brasil"),
                                 ("VEA", "Desarrollados ex-EE.UU.")]),
            ("Renta fija", [("TLT", "Bonos EE.UU. 20+ años"), ("AGG", "Bonos agregados"),
                            ("SHY", "Bonos EE.UU. 1-3 años")]),
            ("Materias primas", [("GLD", "Oro"), ("SLV", "Plata"), ("USO", "Petróleo")]),
        ],
    },
}


def market_name(code: str) -> str:
    return MARKETS[code]["name"]


def sectors(code: str) -> list[tuple[str, list[tuple[str, str]]]]:
    return MARKETS[code]["sectors"]


def company_name(ticker: str) -> str | None:
    for m in MARKETS.values():
        for _, items in m["sectors"]:
            for t, name in items:
                if t == ticker:
                    return name
    return None
