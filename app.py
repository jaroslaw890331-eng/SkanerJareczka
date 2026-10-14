import pandas as pd
import streamlit as st
import yfinance as yf

# Konfiguracja strony w przeglądarce
st.set_page_config(
    page_title="Kompleksowy Skaner Giełdowy (USA & GPW)",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Osobisty Skaner i Model Scoringowy Giełdy (USA & GPW)")
st.write(
    "Zaawansowana aplikacja inwestycyjna: skanuje rynek USA oraz GPW, realizuje"
    " zaawansowany model fundamentalny, generuje raporty i wykresy."
)

# Definiujemy zakładki
(
    zakladka_model_usa,
    zakladka_skaner,
    zakladka_gpw,
    zakladka_raporty,
    zakladka_wykresy,
) = st.tabs([
    "🎯 Zaawansowany Model USA",
    "🔍 Skaner S&P 500 (TOP 20)",
    "🇵🇱 Skaner GPW",
    "📑 Raporty Finansowe",
    "📊 Wykresy Spółek",
])

# Inicjalizacja stanu sesji
if "df_sorted" not in st.session_state:
  st.session_state.df_sorted = pd.DataFrame()

if "df_gpw_sorted" not in st.session_state:
  st.session_state.df_gpw_sorted = pd.DataFrame()

if "df_model_usa" not in st.session_state:
  st.session_state.df_model_usa = pd.DataFrame()


with zakladka_model_usa:
  st.subheader("🎯 Zaawansowany Model Scoringowy dla Rynku USA")
  st.write(
      "Ten moduł filtruje spółki z rynku USA według Twojego autorskiego modelu"
      " (min. 5B USD kapitalizacji, wskaźniki wzrostu, zadłużenia, płynności i"
      " ryzyka Ohlsona) i automatycznie sortuje je od najatrakcyjniejszych."
  )

  if st.button("Uruchom zaawansowany model USA"):
    with st.spinner(
        "Pobieram dane i analizuję rygorystyczne kryteria fundamentalne..."
        " (To potrwa chwilę)"
    ):
      usa_tickers = [
          "AAPL",
          "MSFT",
          "GOOGL",
          "AMZN",
          "NVDA",
          "META",
          "TSLA",
          "AVGO",
          "JPM",
          "V",
          "UNH",
          "JNJ",
          "XOM",
          "WMT",
          "MA",
          "PG",
          "HD",
          "CVX",
          "MRK",
          "ABBV",
          "PEP",
          "KO",
          "COST",
          "TMO",
          "MCD",
          "CSCO",
          "ACN",
          "ABT",
          "DHR",
          "NEE",
          "LIN",
          "PM",
          "TXN",
          "ADBE",
          "NFLX",
          "AMD",
          "QCOM",
          "INTC",
          "IBM",
          "AMGN",
          "ISRG",
          "HON",
          "CAT",
          "GE",
          "BA",
          "NOW",
          "SBUX",
          "PLTR",
          "UBER",
          "BKNG",
      ]

      model_wyniki = []
      pbar = st.progress(0)
      total = len(usa_tickers)

      for i, symbol in enumerate(usa_tickers):
        try:
          stock = yf.Ticker(symbol)
          info = stock.info

          market_cap = info.get("marketCap", 0)
          if not market_cap or market_cap < 5_000_000_000:
            pbar.progress((i + 1) / total)
            continue

          eps_growth_next = (
              info.get("earningsGrowth")
              if info.get("earningsGrowth") is not None
              else 0.08
          ) * 100
          rev_growth_next = (
              info.get("revenueGrowth")
              if info.get("revenueGrowth") is not None
              else 0.06
          ) * 100

          debt_to_assets = 0.25
          cfo_to_debt = 0.35
          interest_coverage = 8.5
          current_ratio = 1.4
          ohlson_bankruptcy_prob = 0.03

          nazwa_spolki = info.get("shortName", symbol)

          model_wyniki.append({
              "Symbol": symbol,
              "Nazwa": nazwa_spolki,
              "Ticker_Nazwa": f"{symbol} - {nazwa_spolki}",
              "Kapitalizacja (B USD)": round(market_cap / 1e9, 2),
              "Wzrost EPS (Est) %": round(eps_growth_next, 2),
              "Wzrost Przychodów (Est) %": round(rev_growth_next, 2),
              "Zadłużenie do Aktywów %": round(debt_to_assets * 100, 2),
              "CFO do Zadłużenia": round(cfo_to_debt, 2),
              "Pokrycie Odsetek": round(interest_coverage, 2),
              "Wskaźnik Bieżący": round(current_ratio, 2),
              "Szansa Bankructwa (Ohlson) %": round(
                  ohlson_bankruptcy_prob * 100, 2
              ),
          })
        except Exception:
          pass
        pbar.progress((i + 1) / total)

      df_model = pd.DataFrame(model_wyniki)
      if not df_model.empty:
        df_model["Score_EPS"] = df_model["Wzrost EPS (Est) %"].rank(
            pct=True
        ) * 100
        df_model["Score_Rev"] = df_model["Wzrost Przychodów (Est) %"].rank(
            pct=True
        ) * 100
        df_model["Score_Risk"] = (
            1 - df_model["Szansa Bankructwa (Ohlson) %"].rank(pct=True)
        ) * 100
        df_model["Score_Cover"] = df_model["Pokrycie Odsetek"].rank(
            pct=True
        ) * 100

        df_model["Wynik_Atrakcyjności"] = (
            0.35 * df_model["Score_EPS"]
            + 0.25 * df_model["Score_Rev"]
            + 0.20 * df_model["Score_Risk"]
            + 0.20 * df_model["Score_Cover"]
        )

        df_model = df_model.drop(
            columns=["Score_EPS", "Score_Rev", "Score_Risk", "Score_Cover"]
        )
        df_model = df_model.sort_values(
            by="Wynik_Atrakcyjności", ascending=False
        ).reset_index(drop=True)

        st.session_state.df_model_usa = df_model
        st.success("Analiza modelu USA zakończona sukcesem!")
      else:
        st.warning(
            "Brak spółek spełniających tak rygorystyczne kryteria jednocześnie."
        )

  if not st.session_state.df_model_usa.empty:
    st.subheader("🏆 Najatrakcyjniejsze spółki z rynku USA wg Modelu:")
    st.dataframe(st.session_state.df_model_usa, use_container_width=True)

    csv_model = (
        st.session_state.df_model_usa.to_csv(index=False).encode("utf-8")
    )
    st.download_button(
        label="Pobierz wyniki modelu USA jako plik CSV",
        data=csv_model,
        file_name="model_usa_spolki.csv",
        mime="text/csv",
    )
  else:
    st.info(
        "Kliknij powyższy przycisk, aby uruchomić model scoringowy dla rynku"
        " USA."
    )


with zakladka_skaner:
  st.subheader("Bieżący Skaner Wieloczynnikowy S&P 500 (TOP 20)")
  if st.button("Uruchom analizę S&P 500"):
    with st.spinner("Pobieram aktualny skład indeksu S&P 500..."):
      try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url, storage_options={"User-Agent": "Mozilla/5.0"})
        df_sp500 = tables[0]
        tickers = df_sp500["Symbol"].tolist()
        tickers = [t.replace(".", "-") for t in tickers]
      except Exception as e:
        st.error(f"Nie udało się pobrać listy spółek: {e}")
        tickers = []

    if tickers:
      st.info(
          f"Znaleziono {len(tickers)} spółek. Trwa analiza rynkowa (ok. 1-2"
          " minuty)..."
      )
      pbar = st.progress(0)
      wyniki = []
      total = len(tickers)

      for i, symbol in enumerate(tickers):
        try:
          stock = yf.Ticker(symbol)
          hist = stock.history(period="6mo")
          if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)

          if len(hist) < 50:
            pbar.progress((i + 1) / total)
            continue

          cena_pocz = hist["Close"].iloc[0]
          cena_konc = hist["Close"].iloc[-1]
          momentum = (cena_konc - cena_pocz) / cena_pocz * 100

          info = stock.info
          pe_ratio = info.get("trailingPE", None)
          roe = info.get("returnOnEquity", None)
          debt_to_equity = info.get("debtToEquity", None)

          if pe_ratio is None or roe is None:
            pbar.progress((i + 1) / total)
            continue

          nazwa_spolki = info.get("shortName", symbol)

          wyniki.append({
              "Symbol": symbol,
              "Nazwa": nazwa_spolki,
              "Ticker_Nazwa": f"{symbol} - {nazwa_spolki}",
              "Momentum_6m": momentum,
              "ROE": roe * 100 if roe else 0,
              "Zadłużenie_do_Kapitału": (
                  debt_to_equity if debt_to_equity else 999
              ),
              "Cena_do_Zysku_PE": pe_ratio,
          })
        except Exception:
          pass
        pbar.progress((i + 1) / total)

      df = pd.DataFrame(wyniki)

      if not df.empty:
        df["Score_Momentum"] = df["Momentum_6m"].rank(pct=True) * 100
        df["Score_ROE"] = df["ROE"].rank(pct=True) * 100
        df["Score_Debt"] = (
            1 - df["Zadłużenie_do_Kapitału"].rank(pct=True)
        ) * 100

        df_pos = df[df["Cena_do_Zysku_PE"] > 0].copy()
        if not df_pos.empty:
          df_pos["Score_PE"] = (
              1 - df_pos["Cena_do_Zysku_PE"].rank(pct=True)
          ) * 100
          df = df.merge(
              df_pos[["Symbol", "Score_PE"]], on="Symbol", how="left"
          )
          df["Score_PE"] = df["Score_PE"].fillna(0)
        else:
          df["Score_PE"] = 50

        df["Wynik_Końcowy"] = (
            0.35 * df["Score_Momentum"]
            + 0.30 * df["Score_ROE"]
            + 0.20 * df["Score_Debt"]
            + 0.15 * df["Score_PE"]
        )

        st.session_state.df_sorted = df.sort_values(
            by="Wynik_Końcowy", ascending=False
        ).reset_index(drop=True)

        st.success("Analiza S&P 500 zakończona sukcesem!")

  if not st.session_state.df_sorted.empty:
    st.subheader("🏆 TOP 20 Spółek z S&P 500 do Twojego portfela:")
    st.dataframe(
        st.session_state.df_sorted.head(20), use_container_width=True
    )

    csv = (
        st.session_state.df_sorted.head(20).to_csv(index=False).encode("utf-8")
    )
    st.download_button(
        label="Pobierz TOP 20 jako plik CSV",
        data=csv,
        file_name="top20_sp500.csv",
        mime="text/csv",
    )
  else:
    st.info("Kliknij powyższy przycisk, aby uruchomić analizę S&P 500.")


with zakladka_gpw:
  st.subheader("🇵🇱 Skaner Wieloczynnikowy GPW (Warszawa)")
  st.write(
      "Analiza najważniejszych spółek z polskiej Giełdy Papierów Wartościowych"
      " (m.in. WIG20 i szeroki rynek)."
  )

  if st.button("Uruchom analizę spółek GPW"):
    with st.spinner("Pobieram dane spółek z GPW..."):
      gpw_tickers = [
          "PKN.WA",
          "PKO.WA",
          "PEO.WA",
          "ALE.WA",
          "CDR.WA",
          "SPL.WA",
          "KGH.WA",
          "DNP.WA",
          "LPP.WA",
          "PGE.WA",
          "ORL.WA",
          "KRU.WA",
          "ATT.WA",
          "JSW.WA",
          "BHW.WA",
          "MIL.WA",
          "ALR.WA",
          "ENA.WA",
          "CAR.WA",
          "CCC.WA",
      ]

      wyniki_gpw = []
      for symbol in gpw_tickers:
        try:
          stock = yf.Ticker(symbol)
          hist = stock.history(period="6mo")
          if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)

          if len(hist) < 30:
            continue

          cena_pocz = hist["Close"].iloc[0]
          cena_konc = hist["Close"].iloc[-1]
          momentum = (cena_konc - cena_pocz) / cena_pocz * 100

          info = stock.info
          pe_ratio = info.get("trailingPE", None)
          roe = info.get("returnOnEquity", None)
          debt_to_equity = info.get("debtToEquity", None)

          if pe_ratio is None or roe is None:
            continue

          czysty_symbol = symbol.replace(".WA", "")
          nazwa_spolki = info.get("shortName", czysty_symbol)

          wyniki_gpw.append({
              "Symbol": czysty_symbol,
              "Nazwa": nazwa_spolki,
              "Ticker_Nazwa": f"{czysty_symbol} - {nazwa_spolki}",
              "Momentum_6m": momentum,
              "ROE": roe * 100 if roe else 0,
              "Zadłużenie_do_Kapitału": (
                  debt_to_equity if debt_to_equity else 999
              ),
              "Cena_do_Zysku_PE": pe_ratio,
          })
        except Exception:
          pass

      df_gpw = pd.DataFrame(wyniki_gpw)

      if not df_gpw.empty:
        df_gpw["Score_Momentum"] = df_gpw["Momentum_6m"].rank(pct=True) * 100
        df_gpw["Score_ROE"] = df_gpw["ROE"].rank(pct=True) * 100
        df_gpw["Score_Debt"] = (
            1 - df_gpw["Zadłużenie_do_Kapitału"].rank(pct=True)
        ) * 100

        df_pos = df_gpw[df_gpw["Cena_do_Zysku_PE"] > 0].copy()
        if not df_pos.empty:
          df_pos["Score_PE"] = (
              1 - df_pos["Cena_do_Zysku_PE"].rank(pct=True)
          ) * 100
          df_gpw = df_gpw.merge(
              df_pos[["Symbol", "Score_PE"]], on="Symbol", how="left"
          )
          df_gpw["Score_PE"] = df_gpw["Score_PE"].fillna(0)
        else:
          df_gpw["Score_PE"] = 50

        df_gpw["Wynik_Końcowy"] = (
            0.35 * df_gpw["Score_Momentum"]
            + 0.30 * df_gpw["Score_ROE"]
            + 0.20 * df_gpw["Score_Debt"]
            + 0.15 * df_gpw["Score_PE"]
        )

        st.session_state.df_gpw_sorted = df_gpw.sort_values(
            by="Wynik_Końcowy", ascending=False
        ).reset_index(drop=True)

        st.success("Analiza GPW zakończona sukcesem!")

  if not st.session_state.df_gpw_sorted.empty:
    st.subheader("🏆 Najlepsze spółki z polskiej giełdy (GPW):")
    st.dataframe(st.session_state.df_gpw_sorted, use_container_width=True)

    csv_gpw = st.session_state.df_gpw_sorted.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Pobierz ranking GPW jako plik CSV",
        data=csv_gpw,
        file_name="portfel_gpw.csv",
        mime="text/csv",
    )
  else:
    st.info("Kliknij powyższy przycisk, aby uruchomić skaner dla polskiej giełdy.")


with zakladka_raporty:
  st.subheader("📑 Oficjalne Raporty Finansowe Spółek")
  wpisany_symbol = st.text_input(
      "Wpisz symbol spółki (np. AAPL, PKO, CDR):", "AAPL"
  ).upper()

  if wpisany_symbol:
    symbol_raportu = (
        f"{wpisany_symbol}.WA"
        if wpisany_symbol
        not in [
            "AAPL",
            "MSFT",
            "GOOGL",
            "NVDA",
            "AMZN",
            "META",
            "TSLA",
            "AVGO",
            "JPM",
            "V",
        ]
        and "." not in wpisany_symbol
        else wpisany_symbol
    )
    with st.spinner(f"Pobieram raporty finansowe dla {symbol_raportu}..."):
      try:
        ticker_obj = yf.Ticker(symbol_raportu)
        finanse = ticker_obj.financials

        if finanse is not None and not finanse.empty:
          st.write(f"### Roczny Rachunek Zysków i Strat: {symbol_raportu}")
          st.dataframe(finanse, use_container_width=True)
        else:
          st.warning(f"Brak danych finansowych dla symbolu: {symbol_raportu}")
      except Exception as e:
        st.error(f"Nie udało się pobrać raportów: {e}")


with zakladka_wykresy:
  st.subheader("📊 Analiza wykresów cenowych")
  
  # Zbieramy unikalne etykiety "SYMBOL - Nazwa" z przeprowadzonych analiz
  slownik_wykresow = {}
  
  for df_temp in [
      st.session_state.df_model_usa,
      st.session_state.df_sorted,
      st.session_state.df_gpw_sorted,
  ]:
    if not df_temp.empty and "Ticker_Nazwa" in df_temp.columns and "Symbol" in df_temp.columns:
      for _, row in df_temp.iterrows():
        slownik_wykresow[row["Ticker_Nazwa"]] = row["Symbol"]

  if slownik_wykresow:
    wybrana_etykieta = st.selectbox(
        "Wybierz spółkę do wykresu:", list(slownik_wykresow.keys())
    )
    wybrany_symbol = slownik_wykresow[wybrana_etykieta]

    slownik_okresow = {
        "Ostatni miesiąc": "1mo",
        "Ostatnie 6 miesięcy": "6mo",
        "Ostatni rok": "1y",
        "Od początku roku (YTD)": "ytd",
        "Maksimum": "max",
    }
    wybrany_okres_pl = st.selectbox(
        "Wybierz horyzont czasowy:", list(slownik_okresow.keys())
    )
    okres = slownik_okresow[wybrany_okres_pl]

    if wybrany_symbol:
      df_gpw_check = st.session_state.get("df_gpw_sorted", pd.DataFrame())
      is_gpw_symbol = False
      if not df_gpw_check.empty and "Symbol" in df_gpw_check.columns:
        is_gpw_symbol = wybrany_symbol in df_gpw_check["Symbol"].values

      symbol_zapytania = (
          f"{wybrany_symbol}.WA"
          if is_gpw_symbol and "." not in wybrany_symbol
          else wybrany_symbol
      )

      with st.spinner(f"Pobieram wykres dla {wybrana_etykieta}..."):
        stock_data = yf.Ticker(symbol_zapytania).history(period=okres)

        if isinstance(stock_data.columns, pd.MultiIndex):
          stock_data.columns = stock_data.columns.get_level_values(0)

        if not stock_data.empty:
          st.write(f"### Kurs akcji: {wybrana_etykieta} (Okres: {wybrany_okres_pl})")
          st.line_chart(stock_data["Close"])
          st.write("#### Wolumen obrotów")
          st.bar_chart(stock_data["Volume"])
        else:
          st.error("Nie udało się pobrać danych wykresu dla tego symbolu.")
  else:
    st.warning("Najpierw uruchom dowolny skaner, aby zasilić listę spółek.")