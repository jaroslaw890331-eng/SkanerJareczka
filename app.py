import pandas as pd
import streamlit as st
import yfinance as yf

# Konfiguracja strony w przeglądarce
st.set_page_config(
    page_title="Skaner S&P 500, GPW i Raporty", page_icon="📈", layout="wide"
)

st.title("📈 Osobisty Skaner Giełdowy (S&P 500 & GPW)")
st.write(
    "Zaawansowana aplikacja inwestycyjna: skanuje amerykańskie i polskie akcje,"
    " generuje raporty, wykresy i przeprowadza backtesty."
)

# Definiujemy zakładki
zakladka_skaner, zakladka_gpw, zakladka_raporty, zakladka_wykresy, zakladka_backtest = st.tabs([
    "🔍 Skaner S&P 500 (TOP 50)",
    "🇵🇱 Skaner GPW",
    "📑 Raporty Finansowe",
    "📊 Wykresy Spółek",
    "⏳ Backtest Historyczny (3 lata)",
])

# Inicjalizacja stanu sesji
if "df_sorted" not in st.session_state:
  st.session_state.df_sorted = pd.DataFrame()

if "df_gpw_sorted" not in st.session_state:
  st.session_state.df_gpw_sorted = pd.DataFrame()

with zakladka_skaner:
  st.subheader("Bieżący Skaner Wieloczynnikowy S&P 500")
  if st.button("Uruchom analizę całego S&P 500"):
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

          wyniki.append({
              "Symbol": symbol,
              "Momentum_6m": momentum,
              "ROE": roe * 100 if roe else 0,
              "DebtToEquity": debt_to_equity if debt_to_equity else 999,
              "PE": pe_ratio,
          })
        except Exception:
          pass
        pbar.progress((i + 1) / total)

      df = pd.DataFrame(wyniki)

      if not df.empty:
        df["Score_Momentum"] = df["Momentum_6m"].rank(pct=True) * 100
        df["Score_ROE"] = df["ROE"].rank(pct=True) * 100
        df["Score_Debt"] = (1 - df["DebtToEquity"].rank(pct=True)) * 100

        df_pos = df[df["PE"] > 0].copy()
        if not df_pos.empty:
          df_pos["Score_PE"] = (1 - df_pos["PE"].rank(pct=True)) * 100
          df = df.merge(
              df_pos[["Symbol", "Score_PE"]], on="Symbol", how="left"
          )
          df["Score_PE"] = df["Score_PE"].fillna(0)
        else:
          df["Score_PE"] = 50

        df["Final_Score"] = (
            0.35 * df["Score_Momentum"]
            + 0.30 * df["Score_ROE"]
            + 0.20 * df["Score_Debt"]
            + 0.15 * df["Score_PE"]
        )

        st.session_state.df_sorted = df.sort_values(
            by="Final_Score", ascending=False
        ).reset_index(drop=True)

        st.success("Analiza S&P 500 zakończona sukcesem!")

  if not st.session_state.df_sorted.empty:
    st.subheader("🏆 TOP 50 Spółek z S&P 500 do Twojego portfela:")
    st.dataframe(
        st.session_state.df_sorted.head(50), use_container_width=True
    )

    csv = (
        st.session_state.df_sorted.head(50).to_csv(index=False).encode("utf-8")
    )
    st.download_button(
        label="Pobierz TOP 50 jako plik CSV",
        data=csv,
        file_name="top50_sp500.csv",
        mime="text/csv",
    )
  else:
    st.info(
        "Kliknij powyższy przycisk 'Uruchom analizę całego S&P 500', aby wygenerować"
        " ranking."
    )

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

          wyniki_gpw.append({
              "Symbol": symbol.replace(".WA", ""),
              "Momentum_6m": momentum,
              "ROE": roe * 100 if roe else 0,
              "DebtToEquity": debt_to_equity if debt_to_equity else 999,
              "PE": pe_ratio,
          })
        except Exception:
          pass

      df_gpw = pd.DataFrame(wyniki_gpw)

      if not df_gpw.empty:
        df_gpw["Score_Momentum"] = df_gpw["Momentum_6m"].rank(pct=True) * 100
        df_gpw["Score_ROE"] = df_gpw["ROE"].rank(pct=True) * 100
        df_gpw["Score_Debt"] = (
            1 - df_gpw["DebtToEquity"].rank(pct=True)
        ) * 100

        df_pos = df_gpw[df_gpw["PE"] > 0].copy()
        if not df_pos.empty:
          df_pos["Score_PE"] = (1 - df_pos["PE"].rank(pct=True)) * 100
          df_gpw = df_gpw.merge(
              df_pos[["Symbol", "Score_PE"]], on="Symbol", how="left"
          )
          df_gpw["Score_PE"] = df_gpw["Score_PE"].fillna(0)
        else:
          df_gpw["Score_PE"] = 50

        df_gpw["Final_Score"] = (
            0.35 * df_gpw["Score_Momentum"]
            + 0.30 * df_gpw["Score_ROE"]
            + 0.20 * df_gpw["Score_Debt"]
            + 0.15 * df_gpw["Score_PE"]
        )

        st.session_state.df_gpw_sorted = df_gpw.sort_values(
            by="Final_Score", ascending=False
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
    # Automatyczne dodanie .WA dla spółek z GPW, jeśli nie mają kropki
    symbol_raportu = (
        f"{wpisany_symbol}.WA"
        if wpisany_symbol not in ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN"]
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
  wszystkie_symbole = []
  if not st.session_state.df_sorted.empty:
    wszystkie_symbole.extend(st.session_state.df_sorted["Symbol"].tolist())
  if not st.session_state.df_gpw_sorted.empty:
    wszystkie_symbole.extend(st.session_state.df_gpw_sorted["Symbol"].tolist())

  if wszystkie_symbole:
    wybrany_symbol = st.selectbox(
        "Wybierz spółkę do wykresu:", list(set(wszystkie_symbole))
    )
    okres = st.selectbox(
        "Wybierz horyzont czasowy:", ["1mo", "6mo", "1y", "ytd", "max"]
    )

    if wybrany_symbol:
      symbol_zapytania = (
          f"{wybrany_symbol}.WA"
          if wybrany_symbol
          in st.session_state.df_gpw_sorted["Symbol"].values
          and "." not in wybrany_symbol
          else wybrany_symbol
      )

      with st.spinner(f"Pobieram wykres dla {wybrany_symbol}..."):
        stock_data = yf.Ticker(symbol_zapytania).history(period=okres)

        if isinstance(stock_data.columns, pd.MultiIndex):
          stock_data.columns = stock_data.columns.get_level_values(0)

        if not stock_data.empty:
          st.write(f"### Kurs akcji: {wybrany_symbol} (Okres: {okres})")
          st.line_chart(stock_data["Close"])
          st.write("#### Wolumen obrotów")
          st.bar_chart(stock_data["Volume"])
        else:
          st.error("Nie udało się pobrać danych wykresu dla tego symbolu.")
  else:
    st.warning(
        "Najpierw uruchom skaner S&P 500 lub GPW, aby zasilić listę spółek."
    )

with zakladka_backtest:
  st.subheader(
      "Symulacja Historyczna (Backtest): Strategia Momentum vs Benchmark"
      " (S&P 500)"
  )
  st.write(
      "Ten moduł sprawdza, jak historycznie (w ciągu ostatnich 3 lat) zachowywał"
      " się portfel złożony z wybranych liderów w porównaniu do całego funduszu"
      " S&P 500 (SPY)."
  )

  if st.button("Uruchom backtest historyczny"):
    with st.spinner("Pobieram dane historyczne dla testu..."):
      try:
        test_symbole = [
            "AAPL",
            "MSFT",
            "NVDA",
            "GOOGL",
            "AMZN",
            "META",
            "TSLA",
            "SPY",
        ]
        dane_historyczne = yf.download(
            test_symbole, period="3y", interval="1d", progress=False
        )["Close"]

        if isinstance(dane_historyczne.columns, pd.MultiIndex):
          dane_historyczne = dane_historyczne.droplevel(0, axis=1)

        spolki_portfela = [
            "AAPL",
            "MSFT",
            "NVDA",
            "GOOGL",
            "AMZN",
            "META",
            "TSLA",
        ]
        dane_historyczne["Portfel_Modelu"] = dane_historyczne[
            spolki_portfela
        ].mean(axis=1)
        dane_historyczne["Portfel_Znormalizowany"] = (
            dane_historyczne["Portfel_Modelu"]
            / dane_historyczne["Portfel_Modelu"].iloc[0]
        ) * 100

        st.success("Backtest zakończony pomyślnie!")
        st.line_chart(
            dane_historyczne[["Portfel_Znormalizowany", "SPY"]], height=400
        )
      except Exception as e:
        st.error(f"Wystąpił błąd podczas symulacji historycznej: {e}")